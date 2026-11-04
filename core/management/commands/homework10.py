from django.core.management.base import BaseCommand

from core.homework10 import run


class Command(BaseCommand):
    help = "Run homework 10 ORM queries (use a separate, empty homework database)."

    def handle(self, *args, **options):
        run(write=self.stdout.write)
