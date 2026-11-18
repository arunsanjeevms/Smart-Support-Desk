"""
Encode every resolved ticket so similar-ticket suggestions answer instantly.

    python manage.py build_similarity_index           # encode new or changed tickets
    python manage.py build_similarity_index --force   # encode everything again

The first run downloads the model (about 90 MB) from Hugging Face; after that
it is loaded from the local cache and works offline.
"""

import time

from django.core.management.base import BaseCommand, CommandError

from apps.similarity.constants import SEMANTIC
from apps.similarity.engines import get_engine, similarity_settings
from apps.similarity.services import build_index


class Command(BaseCommand):
    help = "Encode all resolved tickets for the similar-ticket suggestions (downloads the model on first use)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Encode every ticket again, even if it is up to date.")

    def handle(self, *args, **options):
        config = similarity_settings()
        if config["ENGINE"] != SEMANTIC:
            self.stdout.write("SIMILARITY_ENGINE is set to keyword matching - there is nothing to build.")
            return

        started = time.perf_counter()
        self.stdout.write(f"Loading {config['MODEL']} ...")
        engine = get_engine()
        if engine.name != SEMANTIC:
            raise CommandError(
                f"Could not load {config['MODEL']} (see the log above). Check the internet connection for the "
                "first download, then run this command again. Until then suggestions use keyword matching."
            )
        encoded, total = build_index(engine, force=options["force"])
        self.stdout.write(self.style.SUCCESS(
            f"Similarity index ready: {total} resolved tickets ({encoded} encoded now) "
            f"in {time.perf_counter() - started:.1f}s."
        ))
