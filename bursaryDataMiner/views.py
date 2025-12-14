from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from bursaryDataMiner.models import UserBursaryMatch, Bursary
import logging

# Import your enhanced scraper
from bursaryDataMiner.scraper import enhanced_scrape_bursaries  # Adjust path if needed

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_bursaries(request):
    if request.method == 'POST':
        try:
            logger.info(f"Starting bursary search for user: {request.user.email}")

            # --- SCRAPE NEW BURSARIES FIRST ---
            scrape_result = enhanced_scrape_bursaries(request.user)
            scraped_count = scrape_result.get("total_found", 0)
            scraped_bursaries = scrape_result.get("bursaries", [])

            logger.info(f"Scraped {scraped_count} new bursaries for user: {request.user.email}")

            # --- AI MATCHING WITH UPDATED DATABASE ---
            total_bursaries = Bursary.objects.count()
            logger.info(f"Total bursaries in database after scraping: {total_bursaries}")

            if total_bursaries == 0:
                return JsonResponse({
                    "status": "warning",
                    "message": "No bursaries in database. Please populate database first.",
                    "scraped": scraped_count,
                    "matched": 0,
                    "data": []
                })

            # Try AI matching with existing data
            ai_results = []
            try:
                from bursaryDataMiner.ai_ranker import ai_match_user_to_bursaries
                ai_results = ai_match_user_to_bursaries(request.user, limit=30)
                logger.info(f"AI matching returned {len(ai_results)} results")
            except Exception as ai_error:
                logger.error(f"AI matching failed: {str(ai_error)}")
                # Fallback: Use simple matching from existing UserBursaryMatch records
                try:
                    existing_matches = UserBursaryMatch.objects.filter(
                        user=request.user
                    ).select_related('bursary')[:30]
                    ai_results = []
                    for match in existing_matches:
                        ai_results.append({
                            'title': match.bursary.title or 'Untitled',
                            'url': match.bursary.url or '',
                            'description': (match.bursary.description or '')[:300],
                            'relevance_score': getattr(match, 'relevance_score', 50),
                            'match_quality': getattr(match, 'match_quality', 'Good Match'),
                        })
                    logger.info(f"Fallback: Using {len(ai_results)} existing matches")
                except Exception as fallback_error:
                    logger.error(f"Fallback matching also failed: {str(fallback_error)}")
                    ai_results = []

            return JsonResponse({
                "status": "success" if ai_results else "partial",
                "scraped": scraped_count,
                "matched": len(ai_results),
                "data": ai_results,
                "message": f"{len(ai_results)} matches found. {scraped_count} bursaries scraped."
            })

        except Exception as e:
            logger.error(f"Critical error in search_bursaries: {str(e)}")
            return JsonResponse({
                "status": "error", 
                "message": f"Search failed: {str(e)}",
                "scraped": 0,
                "matched": 0,
                "data": []
            }, status=500)

    return JsonResponse({'error': 'POST request required'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_matches(request):
    try:
        matches = UserBursaryMatch.objects.filter(user=request.user).select_related('bursary')
        matches_data = []
        
        for match in matches:
            # Handle potential None values safely
            title = match.bursary.title or 'Untitled Bursary'
            url = match.bursary.url or ''
            description = match.bursary.description or 'No description available'
            
            # Safely truncate description
            if len(description) > 200:
                description = description[:200] + '...'
            
            matches_data.append({
                'title': title,
                'url': url,
                'description': description,
                'matched_on': match.matched_on.isoformat() if hasattr(match, 'matched_on') and match.matched_on else None,
                'relevance_score': getattr(match, 'relevance_score', None),
                'match_quality': getattr(match, 'match_quality', None),
            })

        return JsonResponse({
            'status': 'success',
            'matches': matches_data,
            'count': len(matches_data)
        })
        
    except Exception as e:
        logger.error(f"Error in get_user_matches: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error retrieving matches: {str(e)}'
        }, status=500)


# Quick test function to populate some sample data
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def populate_sample_bursaries(request):
    """
    Emergency function to add some sample bursaries for testing
    """
    try:
        sample_bursaries = [
            {
                'title': 'Medical Sciences Excellence Bursary 2025',
                'url': 'https://example.com/medical-bursary',
                'description': 'This bursary supports students pursuing medical sciences, including pharmacy, pharmaceutics, and related health sciences fields. Open to undergraduate and postgraduate students with good academic standing.'
            },
            {
                'title': 'Pharmaceutical Industry Development Fund',
                'url': 'https://example.com/pharma-fund',
                'description': 'Supporting future pharmacists and pharmaceutical scientists. Covers tuition, books, and living expenses for students in pharmacology, pharmaceutical chemistry, and pharmacy practice programs.'
            },
            {
                'title': 'Healthcare Professional Training Bursary',
                'url': 'https://example.com/healthcare-bursary',
                'description': 'Financial assistance for healthcare students including pharmacy, nursing, and medical technology. Focus on students from disadvantaged backgrounds with strong academic performance.'
            },
            {
                'title': 'South African Pharmacy Council Student Support',
                'url': 'https://example.com/sapc-support',
                'description': 'Bursary program specifically for pharmacy students studying pharmacognosy, pharmaceutics, and clinical pharmacy practice. Includes mentorship and internship opportunities.'
            },
            {
                'title': 'Chemical Sciences and Pharmaceutical Research Bursary',
                'url': 'https://example.com/chem-pharma-research',
                'description': 'Supporting research-oriented students in pharmaceutical chemistry, drug development, and related chemical sciences. Preference given to postgraduate students.'
            }
        ]
        
        created_count = 0
        for bursary_data in sample_bursaries:
            bursary, created = Bursary.objects.get_or_create(
                title=bursary_data['title'],
                defaults={
                    'url': bursary_data['url'],
                    'description': bursary_data['description']
                }
            )
            if created:
                created_count += 1
                
                # Create a match for the current user
                UserBursaryMatch.objects.get_or_create(
                    user=request.user,
                    bursary=bursary,
                    defaults={
                        'relevance_score': 80,
                        'match_quality': 'Very Good Match'
                    }
                )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Created {created_count} sample bursaries and matches',
            'total_bursaries': Bursary.objects.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating sample data: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_bursaries(request):

    try:
        bursaries = Bursary.objects.all()
        bursary_list = []
        for bursary in bursaries:
            bursary_list.append({
                'title': bursary.title or 'Untitled Bursary',
                'url': bursary.url or '',
                'description': (bursary.description or '')[:300],
            })

        return JsonResponse({
            'status': 'success',
            'data': bursary_list
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error retrieving bursaries: {str(e)}'
        }, status=500)