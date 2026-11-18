"""
Text similarity on tickets: similar resolved tickets and category suggestions.

Similar resolved tickets (``find_similar``):

1. Every resolved ticket's "title. description" is encoded into an embedding.
   Embeddings are cached in the ``similarity_ticketembedding`` collection with the model
   name and a hash of the text, so each ticket is encoded only once.
2. The new title and description are encoded the same way.
3. The cosine similarity between the two (0 = unrelated, 1 = same meaning) is
   the score. Matches under the minimum score are dropped and the best few
   (at most three) are returned.

Category suggestion (``suggest_category``):

1. The new text is compared with past tickets (any status) using the same cached
   embeddings. The 10 closest tickets with a score of at least 0.30 each vote for
   their category, weighted by their score.
2. If one category gets at least half of the votes, it is suggested
   ("based on 4 similar tickets").
3. If no past ticket is close enough, the text is compared with each category's
   label and description instead, so a newly added category can be suggested too.
4. Otherwise nothing is suggested - a wrong guess is worse than none.

Suggestions are advisory: nothing in here changes a ticket.
"""

import hashlib
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from django.db import IntegrityError

from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue
from apps.tickets.constants import TicketStatus
from apps.tickets.models import Ticket

from .constants import SEMANTIC, STRONG_MATCH
from .engines import get_engine, similarity_settings, ticket_text
from .models import TicketEmbedding


@dataclass(frozen=True)
class Match:
    ticket: Ticket
    score: float

    @property
    def strength(self) -> str:
        return "strong" if self.score >= STRONG_MATCH else "possible"


@dataclass(frozen=True)
class SimilarResult:
    matches: list[Match]
    engine: str
    model: str
    compared: int  # how many resolved tickets were compared
    min_score: float


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolved_tickets(exclude_id=None):
    queryset = (
        Ticket.objects.filter(status=TicketStatus.RESOLVED)
        .select_related("category", "resolved_by")
        .order_by("-resolved_at")
    )
    if exclude_id:
        queryset = queryset.exclude(pk=exclude_id)
    return queryset


def minimum_score(engine) -> float:
    config = similarity_settings()
    return config["MIN_SCORE"] if engine.name == SEMANTIC else config["KEYWORD_MIN_SCORE"]


def find_similar(*, title="", description="", limit=None, exclude_id=None, engine=None, min_score=None):
    """Up to ``limit`` resolved tickets (never more than MAX_RESULTS), best match first."""
    config = similarity_settings()
    limit = max(1, min(limit or config["MAX_RESULTS"], config["MAX_RESULTS"]))
    engine = engine or get_engine()
    threshold = minimum_score(engine) if min_score is None else min_score

    query = ticket_text(title, description)
    candidates = list(resolved_tickets(exclude_id))
    if not query or not candidates:
        return SimilarResult([], engine.name, engine.model_name, len(candidates), threshold)

    texts = [ticket_text(ticket.title, ticket.description) for ticket in candidates]
    if engine.needs_index:
        matrix = embeddings_for(candidates, texts, engine)
        scores = matrix @ engine.encode([query])[0]
    else:
        scores = engine.scores(query, texts)

    # Newest first on equal scores (candidates are already newest first).
    order = np.argsort(-scores, kind="stable")
    matches = [Match(candidates[i], round(float(scores[i]), 4)) for i in order if scores[i] >= threshold]
    return SimilarResult(matches[:limit], engine.name, engine.model_name, len(candidates), threshold)


def embeddings_for(tickets: list[Ticket], texts: list[str], engine) -> np.ndarray:
    """Cached embeddings for these tickets, as one row per ticket."""
    stored, _ = refresh_embeddings(tickets, texts, engine)
    return np.array([stored[ticket.pk].vector for ticket in tickets], dtype=np.float32)


def refresh_embeddings(tickets: list[Ticket], texts: list[str], engine) -> tuple[dict, int]:
    """
    Encode (in one batch) the tickets whose embedding is missing or outdated.

    Returns the embeddings by ticket id and how many tickets were encoded now.
    """
    hashes = [text_hash(text) for text in texts]
    stored = {entry.ticket_id: entry for entry in TicketEmbedding.objects.filter(ticket__in=tickets)}

    stale = [
        index
        for index, ticket in enumerate(tickets)
        if (entry := stored.get(ticket.pk)) is None
        or entry.model_name != engine.model_name
        or entry.text_hash != hashes[index]
    ]
    if stale:
        fresh = engine.encode([texts[index] for index in stale])
        for index, vector in zip(stale, fresh):
            ticket = tickets[index]
            entry = stored.get(ticket.pk) or TicketEmbedding(ticket=ticket)
            entry.model_name = engine.model_name
            entry.text_hash = hashes[index]
            entry.vector = [float(value) for value in vector]
            try:
                entry.save()
            except IntegrityError:
                pass  # a parallel request stored the same ticket a moment ago
            stored[ticket.pk] = entry
    return stored, len(stale)


def recent_tickets():
    """Past tickets used for category suggestions (newest first, capped)."""
    limit = similarity_settings()["CATEGORY_MAX_TICKETS"]
    return Ticket.objects.order_by("-created_at")[:limit]


def build_index(engine=None, *, force=False) -> tuple[int, int]:
    """
    Make sure every ticket used by the suggestions has an up-to-date embedding.

    Returns ``(encoded_now, total)``. With ``force`` every ticket is encoded again.
    """
    engine = engine or get_engine()
    tickets = list(recent_tickets())
    if not engine.needs_index or not tickets:
        return 0, len(tickets)
    if force:
        TicketEmbedding.objects.all().delete()
    texts = [ticket_text(ticket.title, ticket.description) for ticket in tickets]
    _, encoded = refresh_embeddings(tickets, texts, engine)
    return encoded, len(tickets)


# ---------------------------------------------------------------------------
# Category suggestion
# ---------------------------------------------------------------------------
SIMILAR_TICKETS = "similar_tickets"
CATEGORY_DESCRIPTION = "category_description"
# A description match must beat the runner-up by this much to count.
DESCRIPTION_MARGIN = 0.05

_category_vectors: dict[tuple[str, str], np.ndarray] = {}


@dataclass(frozen=True)
class CategorySuggestion:
    category: LookupValue
    confidence: float  # share of the vote, or the description score
    basis: str  # SIMILAR_TICKETS or CATEGORY_DESCRIPTION
    matches: int  # similar tickets that voted for the category


@dataclass(frozen=True)
class CategoryResult:
    suggestion: CategorySuggestion | None
    engine: str
    model: str


def suggest_category(*, title="", description="", engine=None) -> CategoryResult:
    """The most likely category for a new ticket, or no suggestion when unsure."""
    config = similarity_settings()
    engine = engine or get_engine()
    semantic = engine.name == SEMANTIC

    def result(suggestion):
        return CategoryResult(suggestion, engine.name, engine.model_name)

    query = ticket_text(title, description)
    active = {c.pk: c for c in LookupValue.objects.of_type(LookupTypeCode.TICKET_CATEGORY).active()}
    if not query or not active:
        return result(None)
    query_vector = engine.encode([query])[0] if semantic else None

    # 1. Vote of the most similar past tickets (only active categories count).
    candidates = [ticket for ticket in recent_tickets() if ticket.category_id in active]
    if candidates:
        texts = [ticket_text(ticket.title, ticket.description) for ticket in candidates]
        if semantic:
            scores = embeddings_for(candidates, texts, engine) @ query_vector
        else:
            scores = engine.scores(query, texts)
        min_score = config["CATEGORY_MIN_SCORE"] if semantic else config["KEYWORD_MIN_SCORE"]
        votes, voters = defaultdict(float), defaultdict(int)
        for index in np.argsort(-scores, kind="stable")[: config["CATEGORY_NEIGHBOURS"]]:
            if scores[index] < min_score:
                break
            category_id = candidates[index].category_id
            votes[category_id] += float(scores[index])
            voters[category_id] += 1
        if votes:
            best = max(votes, key=votes.get)
            share = votes[best] / sum(votes.values())
            if share >= config["CATEGORY_MIN_CONFIDENCE"]:
                return result(CategorySuggestion(active[best], round(share, 3), SIMILAR_TICKETS, voters[best]))
            return result(None)  # similar tickets disagree: better not to guess

    # 2. Nothing similar yet: compare with the category names and descriptions.
    categories = list(active.values())
    texts = [f"{c.label}. {c.description}" if c.description else c.label for c in categories]
    if semantic:
        scores = _category_matrix(engine, texts) @ query_vector
        threshold = config["CATEGORY_DESCRIPTION_MIN_SCORE"]
    else:
        scores = engine.scores(query, texts)
        threshold = config["KEYWORD_MIN_SCORE"]
    order = np.argsort(-scores, kind="stable")
    best_score = float(scores[order[0]])
    runner_up = float(scores[order[1]]) if len(order) > 1 else 0.0
    if best_score >= threshold and best_score - runner_up >= DESCRIPTION_MARGIN:
        return result(CategorySuggestion(categories[order[0]], round(best_score, 3), CATEGORY_DESCRIPTION, 0))
    return result(None)


def _category_matrix(engine, texts: list[str]) -> np.ndarray:
    """Embeddings of the category descriptions, kept in memory (they rarely change)."""
    missing = [text for text in texts if (engine.model_name, text) not in _category_vectors]
    if missing:
        for text, vector in zip(missing, engine.encode(missing)):
            _category_vectors[(engine.model_name, text)] = vector
    return np.array([_category_vectors[(engine.model_name, text)] for text in texts], dtype=np.float32)
