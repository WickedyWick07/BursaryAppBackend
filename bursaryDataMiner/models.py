from django.db import models 
from django.conf import settings 

class Bursary(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    description = models.TextField(blank=True, null=True)  
    date_found = models.DateTimeField(auto_now_add=True)
    application_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title 

class UserBursaryMatch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bursary_matches')
    bursary = models.ForeignKey(Bursary, on_delete=models.CASCADE, related_name='user_matches')
    matched_on = models.DateTimeField(auto_now_add=True)
    match_quality = models.TextField(null=True, blank=True, max_length=50)
    relevance_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} - {self.bursary.title}"


class BursaryEmbedding(models.Model):
    bursary = models.OneToOneField(Bursary, on_delete=models.CASCADE, related_name="embedding")
    vector = models.JSONField(null=True, blank=True)  # store list[float]
    updated_at = models.DateTimeField(auto_now=True)