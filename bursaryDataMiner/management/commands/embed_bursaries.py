from django.core.management.base import BaseCommand 
from bursaryDataMiner.models import Bursary, BursaryEmbedding 
from bursaryDataMiner.ai_matcher import embed_text, build_bursary_corpus

class Command(BaseCommand):
    help = "Create/update AI embeddings for all bursaries"

    def handle(self, *args, **kwargs): 
        total, created = 0, 0
        for b in Bursary.objects.all().iterator():
            corpus = build_bursary_corpus(b)
            vec = embed_text(corpus)
            if not vec: 
                continue 
            obj, was_created = BursaryEmbedding.objects.update_or_create(
                bursary = b, defaults={"vector": vec}
            )

            total += 1
            created += 1 if was_created else 0 
        self.stdout.write(style.SUCCESS(f"Embedded {total} bursaries ({created} new)."))