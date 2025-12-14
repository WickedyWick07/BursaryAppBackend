from django.urls import path
from .views import login, register, fetch_current_user, refresh_token, fetch_all_users
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,)


urlpatterns = [
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('current-user/', fetch_current_user, name='fetch_current_user'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', refresh_token, name='token_refresh'),
    path('fetch-all-users/', fetch_all_users, name='fetch_all_users'),

]
