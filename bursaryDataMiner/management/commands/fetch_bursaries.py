from django.core.management.base import BaseCommand
from bursaryDataMiner.scraper import scrape_bursaries
from bursaryDataMiner.matcher import match_and_save

class Command(BaseCommand):
    help = '''scrape bursary data and matches it to user'''

    def handle(self, *args, **kwargs):
        self.stdout.write("Scraping bursaries...")
        bursaries = scrape_bursaries()
        self.stdout.write(f"Found {len(bursaries)} bursaries.")
        self.stdout.write("Matching bursaries to users...")
        match_and_save(bursaries)

        self.stdout.write(self.style.SUCCESS("Matching complete."))