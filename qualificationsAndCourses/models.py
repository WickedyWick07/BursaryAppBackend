from django.db import models
from users.models import CustomUser 
# Create your models here.
class Qualifications(models.Model):
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='qualifications')
    industry = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    id_document = models.FileField(upload_to='documents/id/', blank=True, null=True)
    transcript = models.FileField(upload_to='documents/transcripts/', blank=True, null=True)
    profile_photo = models.ImageField(upload_to='documents/photos/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.industry})"

class Courses(models.Model): 
    qualification = models.ForeignKey("Qualifications", on_delete=models.CASCADE, related_name='courses')
    grade = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=50)
    def __str__(self): 
        return f"{self.name} ({self.grade})"