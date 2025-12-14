from django.urls import path
from .views import (
    create_qualification,
    create_courses,
    get_qualifications,
    update_qualification,
)

urlpatterns = [
    path('qualifications/', create_qualification, name='create_qualification'),
    path('courses/', create_courses, name='create_courses'),
    path('qualifications/list/', get_qualifications, name='get_qualifications'),
    path('qualifications/<int:pk>/update/', update_qualification, name='update_qualification'),
]
