from django.db import models

class SchoolProfile(models.Model):
    school_name = models.CharField(max_length=255)
    principal_name = models.CharField(max_length=255)
    address = models.TextField()
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    registration_number = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)

    def __str__(self):
        return self.school_name
