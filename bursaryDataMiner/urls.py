from django.urls import path
from .views import search_bursaries, get_user_matches, get_all_bursaries

urlpatterns = [
    path('bursary/search/', search_bursaries, name='search-bursaries'),
    path('bursary/matches/', get_user_matches, name='bursaries-match'),
    path('bursaries/', get_all_bursaries, name='bursaries-list'),
]
