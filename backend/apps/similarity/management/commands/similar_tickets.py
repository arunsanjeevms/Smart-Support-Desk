"""
Show which resolved tickets match a piece of text - handy to see the AI at work.

    python manage.py similar_tickets "I was billed two times for this month's plan"
    python manage.py similar_tickets "authenticator codes keep failing" --engine semantic

By default both engines are shown side by side, with every score (even the
ones under the minimum score that the app would hide), so you can see how the
Sentence Transformers model matches different wording where plain keyword
matching does not.
"""

from django.core.management.base import BaseCommand

from apps.similarity.constants import KEYWORD, SEMANTIC
from apps.similarity.engines import get_engine
from apps.similarity.services import find_similar, minimum_score

TITLES = {SEMANTIC: "Semantic (Sentence Transformers)", KEYWORD: "Keyword (TF-IDF word overlap)"}


class Command(BaseCommand):
    help = "Rank resolved tickets against a piece of text with the similarity engines."

    def add_arguments(self, parser):
        parser.add_argument("text", help="Title and/or description of a new issue.")
        parser.add_argument("--engine", choices=[SEMANTIC, KEYWORD, "both"], default="both")
        parser.add_argument("--limit", type=int, default=3, help="How many tickets to show (max 3).")

    def handle(self, *args, **options):
        self.stdout.write(f'\nNew issue: "{options["text"]}"')
        names = [SEMANTIC, KEYWORD] if options["engine"] == "both" else [options["engine"]]
        for name in names:
            engine = get_engine(name)
            heading = TITLES[engine.name]
            if engine.name != name:
                heading += f"  (the {name} model could not be loaded)"
            threshold = minimum_score(engine)
            result = find_similar(description=options["text"], limit=options["limit"], engine=engine, min_score=-1.0)

            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{heading} - {engine.model_name}"))
            self.stdout.write(f"  compared with {result.compared} resolved tickets, suggestions need >= {threshold:.2f}")
            for rank, match in enumerate(result.matches, start=1):
                shown = match.score >= threshold
                line = f"  {rank}. {match.score:6.3f}  {match.ticket.reference}  {match.ticket.title}"
                self.stdout.write(self.style.SUCCESS(line) if shown else f"{line}  (hidden: below {threshold:.2f})")
        self.stdout.write("")
