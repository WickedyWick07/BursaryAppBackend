# bursaryDataMiner/ai_ranker.py
import numpy as np
from django.utils.timezone import now
from bursaryDataMiner.models import Bursary, BursaryEmbedding, UserBursaryMatch
from bursaryDataMiner.ai_matcher import embed_text, cosine
from bursaryDataMiner.profile_text import user_to_profile_text

QUALITY_SIM_THRESHOLD = 0.35  # drop obvious mismatches
EXCELLENT_SIM_THRESHOLD = 0.60

def hard_filters(bursary: Bursary, user) -> bool:
    """
    Put fast ‘must-have’ checks here if you store structured fields later:
      - deadline not passed
      - field-of-study keywords present
      - min average met (if you extract/store it)
    For now, keep permissive so AI similarity does most of the work.
    """
    # Example deadline check if you add `closing_date` field:
    if hasattr(bursary, "closing_date") and bursary.closing_date:
        if bursary.closing_date < now().date():
            return False
    return True

def ai_match_user_to_bursaries(user, limit=30):
    profile_text = user_to_profile_text(user)
    profile_vec = np.array(embed_text(profile_text), dtype=float)
    if profile_vec.size == 0:
        return []

    # Pull all with embeddings
    qs = BursaryEmbedding.objects.select_related("bursary")
    scored = []

    for be in qs.iterator():
        if not be.vector:
            continue
        b = be.bursary
        if not hard_filters(b, user):
            continue
        bursary_vec = np.array(be.vector, dtype=float)
        sim = cosine(profile_vec, bursary_vec)  # 0..1
        if sim < QUALITY_SIM_THRESHOLD:
            continue  # low quality / irrelevant
        score = int(sim * 100)

        # Optional: small bonus if title contains user’s industry words
        title = (b.title or "").lower()
        industry_boost = 0
        if hasattr(user, "qualifications"):
            inds = { (q.industry or "").lower() for q in user.qualifications.all() }
            if any(i and i in title for i in inds):
                industry_boost = 5
        final_score = min(100, score + industry_boost)

        scored.append({
            "bursary": b,
            "score": final_score,
            "quality": ("Excellent Match" if sim >= EXCELLENT_SIM_THRESHOLD else "Good Match"),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:limit]

    # Persist to UserBursaryMatch (idempotent-ish)
    for item in top:
        UserBursaryMatch.objects.update_or_create(
            user=user, bursary=item["bursary"],
            defaults={
                "relevance_score": item["score"],
                "match_quality": item["quality"],
            }
        )

    # Return a clean payload for APIs
    return [
        {
            "title": s["bursary"].title,
            "url": s["bursary"].url,
            "description": (s["bursary"].description or "")[:300],
            "relevance_score": s["score"],
            "match_quality": s["quality"],
        }
        for s in top
    ]
