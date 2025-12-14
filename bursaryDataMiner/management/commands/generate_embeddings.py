from django.core.management.base import BaseCommand
from bursaryDataMiner.models import Bursary, BursaryEmbedding
from sentence_transformers import SentenceTransformer


class Command(BaseCommand):
    help = "Generate embeddings for all bursaries"

    def handle(self, *args, **kwargs):
        model = SentenceTransformer("all-MiniLM-L6-v2")

        bursaries = Bursary.objects.all()
        self.stdout.write(self.style.NOTICE(f"Found {bursaries.count()} bursaries..."))

        for bursary in bursaries:
            vector = model.encode(bursary.description).tolist()
            emb, _ = BursaryEmbedding.objects.get_or_create(bursary=bursary)
            emb.vector = vector
            emb.save()

        self.stdout.write(self.style.SUCCESS("✅ All embeddings generated and saved!"))
