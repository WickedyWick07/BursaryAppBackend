import re
from difflib import SequenceMatcher
from collections import defaultdict

class BursaryMatcher:
    """
    Advanced bursary filtering system that matches bursaries to user's specific study choices
    """
    
    def __init__(self):
        # Define comprehensive field mappings
        self.field_mappings = {
            "Information Technology (IT) & Computer Science": {
                "primary_keywords": [
                    "computer science", "information technology", "IT", "software engineering",
                    "software development", "programming", "coding", "web development",
                    "cybersecurity", "information systems", "data science", "artificial intelligence",
                    "machine learning", "computer engineering", "network engineering"
                ],
                "secondary_keywords": [
                    "tech", "digital", "computing", "software", "programming", "coding",
                    "database", "networking", "security", "AI", "ML", "data", "analytics",
                    "cloud", "mobile", "app development", "system administration"
                ],
                "course_patterns": [
                    r"computer.{0,10}science", r"information.{0,10}technology", 
                    r"software.{0,10}engineering", r"data.{0,10}science",
                    r"cyber.{0,5}security", r"web.{0,10}development"
                ]
            },
            
            "Business, Finance & Accounting": {
                "primary_keywords": [
                    "business", "finance", "accounting", "commerce", "economics",
                    "management", "marketing", "human resources", "business administration",
                    "financial management", "chartered accountant", "bookkeeping"
                ],
                "secondary_keywords": [
                    "MBA", "BCom", "financial", "economic", "commercial", "admin",
                    "HR", "CTA", "SAICA", "SAIPA", "audit", "tax", "banking"
                ],
                "course_patterns": [
                    r"business.{0,15}administration", r"financial.{0,10}management",
                    r"chartered.{0,10}accountant", r"human.{0,10}resources"
                ]
            },
            
            "Engineering": {
                "primary_keywords": [
                    "engineering", "mechanical engineering", "electrical engineering",
                    "civil engineering", "chemical engineering", "industrial engineering",
                    "mining engineering", "aerospace engineering", "biomedical engineering",
                    "environmental engineering", "structural engineering"
                ],
                "secondary_keywords": [
                    "engineer", "mechanical", "electrical", "civil", "chemical",
                    "industrial", "mining", "aerospace", "biomedical", "environmental",
                    "structural", "technical", "technology"
                ],
                "course_patterns": [
                    r"mechanical.{0,10}engineering", r"electrical.{0,10}engineering",
                    r"civil.{0,10}engineering", r"chemical.{0,10}engineering"
                ]
            },
            
            "Health & Medical Sciences": {
                "primary_keywords": [
                    "medicine", "medical", "nursing", "pharmacy", "physiotherapy",
                    "dentistry", "veterinary", "health sciences", "biomedical sciences",
                    "clinical", "healthcare", "medical technology"
                ],
                "secondary_keywords": [
                    "health", "medical", "clinical", "patient", "hospital",
                    "doctor", "nurse", "pharmacist", "therapist", "healthcare"
                ],
                "course_patterns": [
                    r"medical.{0,10}sciences", r"health.{0,10}sciences",
                    r"biomedical.{0,10}sciences"
                ]
            },
            
            "Law & Legal Studies": {
                "primary_keywords": [
                    "law", "legal studies", "jurisprudence", "legal", "attorney",
                    "advocate", "paralegal", "legal practice", "constitutional law"
                ],
                "secondary_keywords": [
                    "legal", "lawyer", "attorney", "advocate", "court",
                    "justice", "litigation", "contract", "constitutional"
                ],
                "course_patterns": [
                    r"legal.{0,10}studies", r"constitutional.{0,10}law"
                ]
            },
            
            "Education & Teaching": {
                "primary_keywords": [
                    "education", "teaching", "teacher training", "pedagogy",
                    "early childhood development", "educational psychology",
                    "curriculum studies", "education management"
                ],
                "secondary_keywords": [
                    "teaching", "teacher", "educator", "education", "academic",
                    "school", "classroom", "curriculum", "pedagogy", "ECD"
                ],
                "course_patterns": [
                    r"teacher.{0,10}training", r"early.{0,10}childhood.{0,10}development",
                    r"educational.{0,10}psychology"
                ]
            }
        }
        
        # Common exclusion patterns
        self.exclusion_patterns = [
            r"job.{0,10}vacancy", r"employment.{0,10}opportunity",
            r"career.{0,10}fair", r"recruitment", r"hiring",
            r"workshop", r"seminar", r"conference", r"event"
        ]
    
    def calculate_relevance_score(self, bursary_title, bursary_description, user_industries, user_courses):
        """
        Calculate relevance score for a bursary based on user's study choices
        Returns score from 0-100
        """
        if not bursary_title:
            return 0
            
        title_lower = bursary_title.lower()
        description_lower = (bursary_description or "").lower()
        combined_text = f"{title_lower} {description_lower}"
        
        # Check for exclusion patterns first
        for pattern in self.exclusion_patterns:
            if re.search(pattern, combined_text):
                return 0  # Exclude non-bursary content
        
        max_score = 0
        best_match_field = None
        
        # Check against each user industry
        for industry in user_industries:
            if not industry or industry not in self.field_mappings:
                continue
                
            field_data = self.field_mappings[industry]
            score = self._calculate_field_score(combined_text, title_lower, field_data)
            
            if score > max_score:
                max_score = score
                best_match_field = industry
        
        # Boost score for direct course matches
        course_boost = self._calculate_course_match_boost(combined_text, user_courses)
        max_score += course_boost
        
        # Cap at 100
        return min(max_score, 100)
    
    def _calculate_field_score(self, combined_text, title_lower, field_data):
        """Calculate score for a specific field"""
        score = 0
        
        # Primary keyword matches (high weight)
        primary_matches = 0
        for keyword in field_data["primary_keywords"]:
            if keyword.lower() in combined_text:
                if keyword.lower() in title_lower:
                    score += 20  # Higher weight for title matches
                    primary_matches += 1
                else:
                    score += 10  # Lower weight for description matches
                    primary_matches += 1
        
        # Secondary keyword matches (medium weight)
        secondary_matches = 0
        for keyword in field_data["secondary_keywords"]:
            if keyword.lower() in combined_text:
                if keyword.lower() in title_lower:
                    score += 8
                    secondary_matches += 1
                else:
                    score += 4
                    secondary_matches += 1
        
        # Pattern matches (high weight for specific patterns)
        for pattern in field_data["course_patterns"]:
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += 25  # High score for specific course patterns
        
        # Bonus for multiple matches (indicates strong relevance)
        if primary_matches >= 2:
            score += 15
        if secondary_matches >= 3:
            score += 10
            
        return score
    
    def _calculate_course_match_boost(self, combined_text, user_courses):
        """Calculate boost score for direct course name matches"""
        if not user_courses:
            return 0
            
        boost = 0
        for course in user_courses:
            if not course:
                continue
                
            course_lower = course.lower()
            
            # Direct course name match
            if course_lower in combined_text:
                boost += 30
                continue
            
            # Partial course name match
            course_words = course_lower.split()
            matching_words = sum(1 for word in course_words if len(word) > 3 and word in combined_text)
            
            if len(course_words) > 0:
                match_ratio = matching_words / len(course_words)
                if match_ratio >= 0.5:  # At least 50% of course words match
                    boost += int(20 * match_ratio)
        
        return min(boost, 40)  # Cap course boost
    
    def filter_bursaries(self, bursaries, user_industries, user_courses, min_score=30):
        """
        Filter and rank bursaries based on relevance to user's study choices
        
        Args:
            bursaries: List of bursary dictionaries
            user_industries: List of user's industry choices
            user_courses: List of user's course names
            min_score: Minimum relevance score to include (default: 30)
        
        Returns:
            List of filtered and ranked bursaries with relevance scores
        """
        if not bursaries:
            return []
        
        # Ensure inputs are lists
        user_industries = user_industries or []
        user_courses = user_courses or []
        
        filtered_bursaries = []
        
        for bursary in bursaries:
            title = bursary.get("title", "")
            description = bursary.get("description", "")
            
            # Calculate relevance score
            score = self.calculate_relevance_score(title, description, user_industries, user_courses)
            
            # Only include if above minimum threshold
            if score >= min_score:
                bursary_copy = bursary.copy()
                bursary_copy["relevance_score"] = score
                bursary_copy["match_quality"] = self._get_match_quality(score)
                filtered_bursaries.append(bursary_copy)
        
        # Sort by relevance score (highest first)
        filtered_bursaries.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return filtered_bursaries
    
    def _get_match_quality(self, score):
        """Convert numerical score to quality label"""
        if score >= 80:
            return "Excellent Match"
        elif score >= 60:
            return "Very Good Match"
        elif score >= 40:
            return "Good Match"
        else:
            return "Fair Match"
    
    def get_filter_summary(self, original_count, filtered_count, user_industries, user_courses):
        """Generate a summary of the filtering process"""
        summary = {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "filtered_out": original_count - filtered_count,
            "filter_efficiency": round((filtered_count / original_count * 100), 1) if original_count > 0 else 0,
            "user_industries": user_industries,
            "user_courses": user_courses
        }
        return summary


# Integration function for your existing scraper
def apply_bursary_filtering(scraped_bursaries, user):
    """
    Apply advanced filtering to scraped bursaries
    
    Args:
        scraped_bursaries: Raw bursaries from scraping
        user: User object with qualifications
    
    Returns:
        Filtered and ranked bursaries
    """
    
    # Extract user data safely
    user_industries = []
    user_courses = []
    
    try:
        if hasattr(user, 'qualifications') and user.qualifications.exists():
            user_industries = list(user.qualifications.values_list("industry", flat=True))
            user_industries = [industry for industry in user_industries if industry]
            
            for qualification in user.qualifications.all():
                if hasattr(qualification, 'courses'):
                    for course in qualification.courses.all():
                        if hasattr(course, 'name') and course.name:
                            user_courses.append(course.name)
                        elif isinstance(course, dict) and "name" in course and course["name"]:
                            user_courses.append(course["name"])
    
    except Exception as e:
        print(f"⚠️ Warning: Could not extract user data for filtering: {e}")
    
    # Initialize matcher and filter
    matcher = BursaryMatcher()
    
    print(f"\n🔍 FILTERING STAGE")
    print(f"📊 Original bursaries: {len(scraped_bursaries)}")
    print(f"🎯 User industries: {user_industries}")
    print(f"📚 User courses: {user_courses}")
    
    # Apply filtering with different thresholds for different scenarios
    if user_industries or user_courses:
        # User has specific study info - use higher threshold
        filtered_bursaries = matcher.filter_bursaries(
            scraped_bursaries, 
            user_industries, 
            user_courses, 
            min_score=30  # Moderate threshold
        )
    else:
        # User has no specific study info - use lower threshold
        filtered_bursaries = matcher.filter_bursaries(
            scraped_bursaries, 
            [], 
            [], 
            min_score=10  # Lower threshold to be inclusive
        )
    
    # Generate summary
    summary = matcher.get_filter_summary(
        len(scraped_bursaries), 
        len(filtered_bursaries), 
        user_industries, 
        user_courses
    )
    
    print(f"✅ Filtered bursaries: {summary['filtered_count']}")
    print(f"🗑️ Filtered out: {summary['filtered_out']}")
    print(f"📈 Relevance efficiency: {summary['filter_efficiency']}%")
    
    # Show top matches
    if filtered_bursaries:
        print(f"\n🏆 TOP MATCHES:")
        for i, bursary in enumerate(filtered_bursaries[:5]):
            print(f"   {i+1}. [{bursary['relevance_score']}] {bursary['title'][:60]}...")
    
    return filtered_bursaries, summary


# Example usage in your main scraping function
def enhanced_scrape_bursaries(user):
    """
    Enhanced version of scrape_bursaries that includes filtering
    """
    try:
        # Step 1: Run the original scraping
        print("🚀 SCRAPING STAGE")
        raw_bursaries = scrape_bursaries(user)  # Your existing function
        
        if not raw_bursaries:
            print("❌ No bursaries found during scraping")
            return []
        
        # Step 2: Apply advanced filtering
        filtered_bursaries, filter_summary = apply_bursary_filtering(raw_bursaries, user)
        
        # Step 3: Save filtered results to database (optional)
        # This ensures only relevant matches are stored
        save_filtered_bursaries_to_db(filtered_bursaries, user)
        
        return {
            "bursaries": filtered_bursaries,
            "summary": filter_summary,
            "total_found": len(raw_bursaries),
            "relevant_matches": len(filtered_bursaries)
        }
        
    except Exception as e:
        print(f"❌ Error in enhanced scraping: {e}")
        return {"bursaries": [], "error": str(e)}


def save_filtered_bursaries_to_db(filtered_bursaries, user):
    """
    Save only the filtered, relevant bursaries to database
    """
    try:
        from bursaryDataMiner.models import Bursary, UserBursaryMatch
        
        saved_count = 0
        for bursary_data in filtered_bursaries:
            # Create or get bursary
            bursary, created = Bursary.objects.get_or_create(
                url=bursary_data["url"],
                defaults={
                    "title": bursary_data["title"],
                    "description": bursary_data.get("description", "")[:2000],
                    "relevance_score": bursary_data.get("relevance_score", 0)
                }
            )
            
            # Create user match with relevance score
            match, match_created = UserBursaryMatch.objects.get_or_create(
                user=user,
                bursary=bursary,
                defaults={
                    "relevance_score": bursary_data.get("relevance_score", 0),
                    "match_quality": bursary_data.get("match_quality", "Fair Match")
                }
            )
            
            if match_created:
                saved_count += 1
        
        print(f"💾 Saved {saved_count} new relevant matches to database")
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")