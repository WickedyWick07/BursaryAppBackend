# Replace or create this file
def user_to_profile_text(user):
    """Build rich contextual profile for embedding"""
    from bursaryDataMiner.enhanced_ai_matcher import build_rich_user_profile
    return build_rich_user_profile(user)