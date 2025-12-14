from django.db import models
from users.models import CustomUser
from qualificationsAndCourses.models import Qualifications, Courses

class Bursary(models.Model):
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bursaries')
    qualification = models.ForeignKey(Qualifications, on_delete=models.CASCADE, related_name='bursaries')
    title = models.CharField(max_length=250)
    url = models.URLField(max_length=500)
    found_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}"
