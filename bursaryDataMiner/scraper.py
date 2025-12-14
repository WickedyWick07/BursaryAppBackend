import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import re
import numpy as np
from django.utils.timezone import now
from django.db import transaction
from bursaryDataMiner.models import Bursary, UserBursaryMatch
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Thresholds for AI matching
MINIMUM_SIM_THRESHOLD = 0.10
GOOD_SIM_THRESHOLD = 0.18
EXCELLENT_SIM_THRESHOLD = 0.28

# ============================================================================
# REQUESTS SESSION WITH RETRY LOGIC
# ============================================================================

def get_resilient_session():
    """Create requests session with automatic retries and proper SSL handling"""
    import urllib3
    
    # Suppress SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    session = requests.Session()
    
    # Retry strategy: retry on connection errors, timeouts, 500/502/503/504
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Disable SSL verification for problematic sites (optional - be careful)
    session.verify = False
    
    return session


# Base sites configuration
BASE_BURSARY_SITES = [
    "https://www.zabursaries.co.za/",
    "https://allbursaries.co.za/",
    "https://www.graduates24.com/bursaries/",
    "https://studytrust.org.za/bursaries/",
    "https://www.studentroom.co.za/category/bursaries/",
    "https://onlinebursaries.co.za/",
    "https://bursariesafrica.co.za/",
    "https://bursariesguru.co.za/",
    "https://www.bursariesportal.co.za/",
    "https://sagovjobs.co.za/category/bursaries/",
    "https://bursaries.co.za/",
    "https://www.gostudy.net/bursaries",
]

UNIVERSITY_BURSARY_SITES = [
    "https://www.unisa.ac.za/sites/Student-Affairs-&-SRC",
    "https://www.boston.ac.za/bursaries",
    "https://www.wits.ac.za/study-at-wits/scholarships-and-bursaries",
    "https://www.uj.ac.za/student-finance/bursaries",
    "https://www.up.ac.za/article/bursaries-and-loans",
    "https://finaid.mandela.ac.za/Bursaries",
    "https://finaid.sun.ac.za",
    "https://www.cut.ac.za/fees-bursaries-and-loans",
    "http://studies.nwu.ac.za/studies/bursaries",
    "https://www.smu.ac.za/Financial-Aid/Students",
    "https://www.univen.ac.za/students/scholarships",
    "https://www.ufs.ac.za/kovsielife/unlisted-pages/finaid",
    "https://www.dut.ac.za/student_services/bursaries",
]

COMPANY_BURSARY_SITES = [
    "https://www.standardbank.com/careers/early-careers",
    "https://www.idc.co.za/bursaries",
    "https://www.nedbank.co.za/careers/youth-talent/the-2025-nedbank-external-bursary-programme",
    "https://fasset.org.za/Bursaries",
    "https://www.investec.com/tertiary-bursary-programme",
    "https://ttibursaries.co.za/students",
]

GOVERNMENT_BURSARY_SITES = [
    "https://applyonline.isfap.org.za",
    "http://www.dffe.gov.za/bursaries",
    "https://www.tourism.gov.za/Careers/pages/bursaries",
    "https://www.dsac.gov.za/DSAC-Bursaries-for-2025-Heritage-Related-Studies",
    "https://www.mict.org.za/bursaries",
    "https://www.sasseta.org.za/Learners",
]

INDUSTRY_SPECIFIC_SITES = {
    "Health & Medical Sciences": [
        "https://www.nrf.ac.za/nrf-for-post-graduate-students",
        "https://www.sansa.org.za/bursaries",
        "https://nstf.org.za/available-bursaries-undergraduates",
    ],
}


# ============================================================================
# MATCHER
# ============================================================================

class ImprovedBursaryMatcher:
    """Simplified matcher focused on recall over precision"""

    def __init__(self):
        self.field_mappings = {
            "Health & Medical Sciences": {
                "keywords": [
                    "medicine", "medical", "nursing", "pharmacy", "pharmacology",
                    "pharmacist", "physiotherapy", "dentistry", "veterinary", "health sciences",
                    "biomedical", "clinical", "public health", "pharmaceutical",
                    "health care", "healthcare", "patient care", "treatment", "diagnosis"
                ]
            },
            "Information Technology (IT) & Computer Science": {
                "keywords": [
                    "computer science", "IT", "software", "programming", "data science",
                    "cybersecurity", "web development", "artificial intelligence",
                    "technology", "developer", "engineer", "systems", "network"
                ]
            },
            "Business, Finance & Accounting": {
                "keywords": [
                    "business", "finance", "accounting", "commerce", "management",
                    "economics", "investment", "banking", "audit"
                ]
            },
            "Engineering": {
                "keywords": [
                    "engineering", "mechanical", "civil", "electrical", "chemical",
                    "industrial", "mining", "structural", "design"
                ]
            },
        }
        
        self.generic_indicators = [
            "bursary", "scholarship", "funding", "grant", "financial aid",
            "award", "support", "assistance", "student aid"
        ]
        
        self.exclusion_patterns = [
            r"job\s+vacanc", r"employme.*opportunit", r"recruitment",
            r"how\s+to\s+apply", r"application\s+tips", r"interview",
            r"motivational\s+letter", r"cv\s+writing"
        ]

    def is_likely_bursary_page(self, title, description):
        """Check if this looks like a bursary opportunity"""
        if not title:
            return False
        
        combined = f"{title} {description}".lower()
        
        # Hard exclusions
        for pattern in self.exclusion_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return False
        
        # Must have at least one generic indicator
        has_generic = any(term in combined for term in self.generic_indicators)
        return has_generic

    def calculate_basic_score(self, title, description, user_industries, user_courses):
        """Calculate relevance score based on keyword matches"""
        if not title:
            return 0
        
        combined = f"{title} {description}".lower()
        score = 0
        
        # Check for user's industries
        for industry in user_industries:
            if industry:
                industry_lower = industry.lower()
                if industry_lower in combined:
                    score += 30
                    break
        
        # Check for user's specific courses
        for course in user_courses:
            if course:
                course_lower = course.lower()
                if course_lower in combined:
                    score += 25
                    break
        
        # Check for generic education indicators
        education_terms = ["undergraduate", "postgraduate", "tertiary", "university",
                          "degree", "student", "academic", "higher education"]
        if any(term in combined for term in education_terms):
            score += 15
        
        # Bonus for bursary indicators
        if any(term in combined for term in self.generic_indicators):
            score += 10
        
        # Fallback
        if score == 0 and len(description) > 50:
            score = 10
        
        return min(score, 100)


# ============================================================================
# SCRAPER
# ============================================================================

def extract_all_links(site_url, session):
    """Extract all links from a page"""
    links = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = session.get(site_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "").strip()
            text = a_tag.get_text(strip=True)
            
            if href and text and len(text) > 3:
                full_url = urljoin(site_url, href)
                
                # Skip non-HTML URLs
                if any(skip in full_url.lower() for skip in [
                    'logout', 'login', 'register', '#', 'javascript',
                    '.pdf', '.doc', '.docx', '.zip', '.jpg', '.png', '.gif',
                    'mailto:', 'tel:', 'ftp:'
                ]):
                    continue
                
                links.append((full_url, text))
        
        # Remove duplicates
        seen = set()
        unique_links = []
        for url, text in links:
            if url not in seen:
                seen.add(url)
                unique_links.append((url, text))
        
        logger.info(f"Extracted {len(unique_links)} unique links from {site_url}")
        return unique_links
    
    except Exception as e:
        logger.error(f"Error extracting links from {site_url}: {e}")
        return links


def fetch_page_content(url, session):
    """Fetch and extract content from a page"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = session.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script/style tags
        for tag in soup(["script", "style"]):
            tag.decompose()
        
        # Extract text
        content_selectors = [".content", ".main-content", ".post-content", ".entry-content",
                            "article", ".article", "main"]
        
        content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(" ", strip=True)
                break
        
        if not content:
            content = soup.get_text(" ", strip=True)
        
        return content[:800]
    
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return ""


def scrape_site_improved(site_url, user_industries, user_courses, existing_urls, matcher, session):
    """Scrape a single site"""
    scraped_bursaries = []
    
    try:
        links = extract_all_links(site_url, session)
        
        if not links:
            logger.info(f"No links found on {site_url}")
            return scraped_bursaries
        
        logger.info(f"Processing {min(len(links), 40)} links from {site_url}")
        
        for url, title in links[:40]:
            if url in existing_urls:
                continue
            
            description = fetch_page_content(url, session)
            
            if not description:
                continue
            
            if not matcher.is_likely_bursary_page(title, description):
                continue
            
            score = matcher.calculate_basic_score(title, description, user_industries, user_courses)
            
            if score > 0:
                bursary_data = {
                    "url": url,
                    "title": title,
                    "description": description,
                    "relevance_score": score
                }
                scraped_bursaries.append(bursary_data)
                logger.info(f"Found: [{score}] {title[:50]}")
            
            # Small delay between requests
            time.sleep(random.uniform(0.5, 1.5))
        
        return scraped_bursaries
    
    except Exception as e:
        logger.error(f"Error scraping {site_url}: {e}")
        return scraped_bursaries


def enhanced_scrape_bursaries(user):
    """Main scraping function"""
    session = get_resilient_session()
    
    try:
        logger.info(f"Starting scraping for {getattr(user, 'email', 'Unknown')}")
        
        # Extract user info
        user_industries, user_courses = [], []
        if hasattr(user, 'qualifications') and user.qualifications.exists():
            user_industries = [q.industry for q in user.qualifications.all() if q.industry]
            for qual in user.qualifications.all():
                if hasattr(qual, 'courses'):
                    for course in qual.courses.all():
                        if hasattr(course, 'name') and course.name:
                            user_courses.append(course.name)
        
        logger.info(f"Industries: {user_industries}")
        logger.info(f"Courses: {user_courses}")
        
        existing_urls = set(Bursary.objects.values_list("url", flat=True))
        matcher = ImprovedBursaryMatcher()
        
        # Build sites list
        sites = []
        for industry in user_industries:
            if industry in INDUSTRY_SPECIFIC_SITES:
                sites.extend(INDUSTRY_SPECIFIC_SITES[industry])
        
        sites.extend(BASE_BURSARY_SITES)
        sites.extend(UNIVERSITY_BURSARY_SITES)
        sites.extend(COMPANY_BURSARY_SITES)
        sites.extend(GOVERNMENT_BURSARY_SITES)
        
        unique_sites = list(dict.fromkeys(sites))
        logger.info(f"Scraping {len(unique_sites)} sites")
        
        all_bursaries = []
        
        for i, site in enumerate(unique_sites):
            logger.info(f"\n[{i+1}/{len(unique_sites)}] {site}")
            
            site_bursaries = scrape_site_improved(site, user_industries, user_courses, 
                                                   existing_urls, matcher, session)
            
            if site_bursaries:
                all_bursaries.extend(site_bursaries)
                
                # Save to DB
                for bursary_data in site_bursaries:
                    bursary_obj, _ = Bursary.objects.get_or_create(
                        url=bursary_data["url"],
                        defaults={
                            "title": bursary_data["title"],
                            "description": bursary_data["description"]
                        }
                    )
                    
                    UserBursaryMatch.objects.get_or_create(
                        user=user,
                        bursary=bursary_obj,
                        defaults={
                            "relevance_score": bursary_data["relevance_score"],
                            "match_quality": "Good Match"
                        }
                    )
            
            time.sleep(random.uniform(1, 2))
        
        all_bursaries.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        logger.info(f"\nTotal found: {len(all_bursaries)}")
        if all_bursaries:
            logger.info("Top 5:")
            for i, b in enumerate(all_bursaries[:5], 1):
                logger.info(f"  {i}. [{b['relevance_score']}] {b['title'][:60]}")
        
        return {
            "matches": all_bursaries,
            "scraped": len(all_bursaries),
            "status": "complete",
            "message": f"{len(all_bursaries)} bursaries found"
        }
    
    except Exception as e:
        logger.error(f"Critical error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"matches": [], "scraped": 0, "status": "error", "message": str(e)}
    
    finally:
        session.close()