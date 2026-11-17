from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class SupportDeskUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Administrators are part of the support team.
        extra_fields.setdefault("role", User.Role.AGENT)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Application user. The ``role`` decides what the person can do:

    * **Requester** - raises tickets and follows their own tickets.
    * **Support Agent** - sees every ticket, changes status, writes resolutions
      and manages configuration values.
    """

    class Role(models.TextChoices):
        REQUESTER = "requester", "Requester"
        AGENT = "agent", "Support Agent"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REQUESTER, db_index=True)
    job_title = models.CharField(max_length=80, blank=True)

    REQUIRED_FIELDS = ["email"]

    objects = SupportDeskUserManager()

    class Meta:
        ordering = ["first_name", "last_name", "username"]

    def __str__(self):
        return self.display_name

    @property
    def is_agent(self) -> bool:
        return self.role == self.Role.AGENT

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username

    @property
    def initials(self) -> str:
        parts = [p for p in (self.first_name, self.last_name) if p]
        if not parts:
            return self.username[:2].upper()
        return "".join(p[0] for p in parts).upper()[:2]
