"""
Text similarity engines used to suggest resolved tickets.

``SemanticEngine`` (the default)
    A pretrained, open-source Sentence Transformers model
    (``sentence-transformers/all-MiniLM-L6-v2``) runs locally on the CPU and
    turns a text into a list of 384 numbers - an *embedding*. Texts with the
    same meaning get embeddings that point in the same direction, even when
    they share no words ("billed two times" ~ "charged twice"). The similarity
    of two texts is the cosine of the angle between their embeddings.

``KeywordEngine`` (fallback)
    Classic TF-IDF word overlap. It needs no model, so it is used when the
    model cannot be loaded (e.g. no internet for the first download) and by
    the fast API tests. It only finds tickets that use the same words.
"""

import importlib.util
import logging
import math
import re
import threading
import time
from collections import Counter

import numpy as np
from django.conf import settings

from .constants import KEYWORD, SEMANTIC

logger = logging.getLogger(__name__)

# After a failed model load, wait this long before trying again.
RETRY_AFTER_SECONDS = 300


def similarity_settings() -> dict:
    return settings.SUPPORT_DESK["SIMILARITY"]


def ticket_text(title: str, description: str) -> str:
    """The text that gets compared: the title (most telling) followed by the description."""
    title = " ".join((title or "").split())
    description = " ".join((description or "").split())
    if title and description:
        separator = " " if title[-1] in ".!?" else ". "
        return f"{title}{separator}{description}"
    return title or description


def semantic_installed() -> bool:
    """True when the sentence-transformers package is installed."""
    return importlib.util.find_spec("sentence_transformers") is not None


# ---------------------------------------------------------------------------
# Sentence Transformers
# ---------------------------------------------------------------------------
class SemanticEngine:
    name = SEMANTIC
    needs_index = True  # resolved tickets are encoded once and cached in MongoDB

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._load_lock = threading.Lock()
        # The tokenizer is not safe to use from several threads at once.
        self._encode_lock = threading.Lock()

    def load(self):
        """Load the model (downloaded from Hugging Face on first use, then cached on disk)."""
        if self._model is None:
            with self._load_lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    from transformers.utils import logging as transformers_logging

                    transformers_logging.disable_progress_bar()  # no download/loading bars in the server log
                    started = time.perf_counter()
                    try:
                        # Already downloaded: load from the local cache without going online.
                        self._model = SentenceTransformer(self.model_name, device="cpu", local_files_only=True)
                    except OSError:
                        # First run: download the model from Hugging Face (about 90 MB).
                        self._model = SentenceTransformer(self.model_name, device="cpu")
                    logger.info("Loaded %s in %.1fs", self.model_name, time.perf_counter() - started)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """One normalised embedding per text (so a dot product is the cosine similarity)."""
        model = self.load()
        with self._encode_lock:
            vectors = model.encode(
                texts,
                batch_size=32,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        return np.asarray(vectors, dtype=np.float32)


# ---------------------------------------------------------------------------
# TF-IDF keywords
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    """a about after again all also am an and any are as at be been before being but by can cannot
    could did do does doing don for from had has have having he her here his how i if in into is it
    its just me more most my no not now of off on once only or other our out over own please same she
    should so some still such than that the their them then there these they this those through to too
    under until up us very was we were what when where which while who why will with would you your""".split()
)


def _stem(word: str) -> str:
    """Very light stemming so "charged", "charges" and "charge" count as one word."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def keywords(text: str) -> list[str]:
    return [_stem(word) for word in _TOKEN_RE.findall(text.lower()) if word not in _STOPWORDS and len(word) > 1]


class KeywordEngine:
    name = KEYWORD
    model_name = "TF-IDF keywords"
    needs_index = False

    def scores(self, query: str, texts: list[str]) -> np.ndarray:
        """Cosine similarity of TF-IDF word weights between the query and each text."""
        documents = [Counter(keywords(text)) for text in texts]
        query_counts = Counter(keywords(query))
        total = len(documents)
        document_frequency = Counter(term for document in documents for term in document)

        def weights(counts: Counter) -> dict[str, float]:
            return {
                term: (1 + math.log(count)) * (math.log((1 + total) / (1 + document_frequency[term])) + 1)
                for term, count in counts.items()
            }

        def norm(vector: dict[str, float]) -> float:
            return math.sqrt(sum(value * value for value in vector.values()))

        query_vector = weights(query_counts)
        query_norm = norm(query_vector)
        result = np.zeros(total, dtype=np.float32)
        if not query_norm:
            return result
        for index, counts in enumerate(documents):
            vector = weights(counts)
            vector_norm = norm(vector)
            if vector_norm:
                dot = sum(weight * vector.get(term, 0.0) for term, weight in query_vector.items())
                result[index] = dot / (query_norm * vector_norm)
        return result


# ---------------------------------------------------------------------------
# Choosing an engine
# ---------------------------------------------------------------------------
_semantic_engines: dict[str, SemanticEngine] = {}
_failed_at: dict[str, float] = {}
_engines_lock = threading.Lock()


def get_engine(name: str | None = None):
    """
    The configured engine, ready to use.

    If the Sentence Transformers model cannot be loaded, fall back to keyword
    matching (and try the model again a few minutes later).
    """
    config = similarity_settings()
    name = name or config["ENGINE"]
    if name != SEMANTIC:
        return KeywordEngine()

    model_name = config["MODEL"]
    failed = _failed_at.get(model_name)
    if failed is not None and time.monotonic() - failed < RETRY_AFTER_SECONDS:
        return KeywordEngine()

    with _engines_lock:
        engine = _semantic_engines.setdefault(model_name, SemanticEngine(model_name))
    try:
        engine.load()
    except Exception:  # not installed, no internet for the first download, ...
        logger.warning("Could not load %s - using keyword matching instead.", model_name, exc_info=True)
        _failed_at[model_name] = time.monotonic()
        return KeywordEngine()
    _failed_at.pop(model_name, None)
    return engine


def warm_up_in_background():
    """
    Load the model in a background thread when the web server starts.

    Importing the libraries takes a while (up to ~20 seconds on Windows), so
    doing it at start-up means the first "Find similar tickets" click is fast.
    """
    config = similarity_settings()
    if not (config["ENABLED"] and config["ENGINE"] == SEMANTIC and config.get("PRELOAD", True)):
        return
    threading.Thread(target=get_engine, name="similarity-warm-up", daemon=True).start()
