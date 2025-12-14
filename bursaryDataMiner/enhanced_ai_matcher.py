# bursaryDataMiner/enhanced_ai_matcher.py
import numpy as np
from django.utils.timezone import now
from django.db import transaction
from bursaryDataMiner.models import Bursary, BursaryEmbedding, UserBursaryMatch
from bursaryDataMiner.ai_matcher import embed_text, cosine, build_bursary_corpus
import logging

logger = logging.getLogger(__name__)

# Adjusted thresholds based on typical embedding similarity ranges
MINIMUM_SIM_THRESHOLD = 0.15   # Very permissive minimum
GOOD_SIM_THRESHOLD = 0.25      # Good match
EXCELLENT_SIM_THRESHOLD = 0.35 # Excellent match (lowered from 0.60)

def build_user_profile(user):
    """Build simple, focused user profile"""
    parts = []
    
    parts.append("Student seeking educational funding")
    
    if hasattr(user, 'qualifications') and user.qualifications.exists():
        for qual in user.qualifications.all():
            if qual.industry:
                parts.append(f"Studying {qual.industry}")
            
            if hasattr(qual, 'courses'):
                for course in qual.courses.all():
                    if hasattr(course, 'name'):
                        parts.append(f"Taking {course.name}")
    
    parts.extend([
        "Need bursary support",
        "Looking for scholarship funding",
        "Tertiary education financial assistance"
    ])
    
    return " | ".join(parts)


def build_bursary_text(bursary):
    """Build text corpus for bursary"""
    parts = []
    
    if bursary.title:
        parts.append(bursary.title)
    if bursary.description:
        parts.append(bursary.description[:500])
    
    parts.extend([
        "Educational opportunity",
        "Student funding",
        "Academic support"
    ])
    
    return " | ".join(parts)


@transaction.atomic
def ai_match_user_to_bursaries(user, limit=50):
    """Simplified AI matching with realistic thresholds"""
    try:
        logger.info(f"AI matching for {getattr(user, 'email', 'Unknown')}")
        
        # Build embeddings
        profile_text = build_user_profile(user)
        profile_vec = np.array(embed_text(profile_text), dtype=float)
        
        if profile_vec.size == 0:
            logger.error("Failed to embed user profile")
            return []
        
        # Get all bursaries
        bursary_qs = Bursary.objects.all()
        logger.info(f"Processing {bursary_qs.count()} bursaries")
        
        matches = []
        
        for bursary in bursary_qs.iterator():
            bursary_text = build_bursary_text(bursary)
            bursary_vec = np.array(embed_text(bursary_text), dtype=float)
            
            if bursary_vec.size == 0:
                continue
            
            # Calculate similarity
            similarity = cosine(profile_vec, bursary_vec)
            
            if similarity < MINIMUM_SIM_THRESHOLD:
                continue
            
            # Determine quality
            if similarity >= EXCELLENT_SIM_THRESHOLD:
                quality = "Excellent Match"
            elif similarity >= GOOD_SIM_THRESHOLD:
                quality = "Very Good Match"
            else:
                quality = "Good Match"
            
            score = int(similarity * 100)
            
            matches.append({
                "bursary": bursary,
                "score": score,
                "quality": quality,
                "similarity": similarity
            })
        
        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        top_matches = matches[:limit]
        
        # Save to DB
        for match in top_matches:
            UserBursaryMatch.objects.update_or_create(
                user=user,
                bursary=match["bursary"],
                defaults={
                    "relevance_score": match["score"],
                    "match_quality": match["quality"]
                }
            )
        
        # Return response
        response = []
        for match in top_matches:
            response.append({
                "title": match["bursary"].title or "Untitled",
                "url": match["bursary"].url or "",
                "description": (match["bursary"].description or "")[:400],
                "relevance_score": match["score"],
                "match_quality": match["quality"]
            })
        
        logger.info(f"AI matching returned {len(response)} matches")
        return response
    
    except Exception as e:
        logger.error(f"AI matching error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []