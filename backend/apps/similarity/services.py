"""
Find resolved tickets that look like a new issue.

1. Every resolved ticket's "title. description" is encoded into an embedding.
   Embeddings are cached in the ``similarity_ticketembedding`` collection with the model
   name and a hash of the text, so each ticket is encoded only once.
2. The new title and description are encoded the same way.
3. The cosine similarity between the two (0 = unrelated, 1 = same meaning) is
   the score. Matches under the minimum score are dropped and the best few
   (at most three) are returned.

Suggestions are advisory: nothing in here changes a ticket.
"""

import hashlib
from dataclasses import dataclass

import numpy as np
from django.db import IntegrityError

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


def build_index(engine=None, *, force=False) -> tuple[int, int]:
    """
    Make sure every resolved ticket has an up-to-date embedding.

    Returns ``(encoded_now, total)``. With ``force`` every ticket is encoded again.
    """
    engine = engine or get_engine()
    tickets = list(resolved_tickets())
    if not engine.needs_index or not tickets:
        return 0, len(tickets)
    if force:
        TicketEmbedding.objects.all().delete()
    texts = [ticket_text(ticket.title, ticket.description) for ticket in tickets]
    _, encoded = refresh_embeddings(tickets, texts, engine)
    return encoded, len(tickets)
