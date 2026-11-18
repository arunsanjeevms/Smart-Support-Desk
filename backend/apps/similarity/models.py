from django.db import models
from django_mongodb_backend.fields import ArrayField

from apps.tickets.models import Ticket


class TicketEmbedding(models.Model):
    """
    Cached embedding (a list of numbers that captures the meaning of a text)
    for one resolved ticket.

    The model name and a hash of the text are stored with the vector, so the
    ticket is only encoded again when its text or the model changes. The whole
    collection can be deleted at any time - it is rebuilt on the next search
    or with ``python manage.py build_similarity_index``.
    """

    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="embedding")
    model_name = models.CharField(max_length=200)
    text_hash = models.CharField(max_length=64)
    vector = ArrayField(models.FloatField())
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ticket_id} ({self.model_name})"
