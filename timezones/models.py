from django.db import models

# Create your models here.
class Country(models.Model):
    code = models.CharField(max_length=5)
    name = models.CharField(max_length=255)
    primary_language = models.CharField(max_length=255)

class Cheers(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    raw = models.CharField(max_length=255)
    pronunciation = models.CharField(max_length=255)

