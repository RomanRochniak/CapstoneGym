from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date

from django.contrib.auth import get_user_model
# Create your models here.

class User(AbstractUser):
    pass

class Trainer(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='trainers/', blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)

    def get_photo(self):
        if self.photo:
            return self.photo.url
        if self.photo_url:
            return self.photo_url
        return ""

    def __str__(self):
        return self.name


class TrainingProgram(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="memberships")
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name="memberships")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        indexes = [
            models.Index(fields=['user', 'program', 'status']),
        ]

    def is_active(self):
        return self.status == 'active' and self.start_date <= date.today() <= self.end_date

    def is_expired(self):
        return self.status == 'expired' or self.end_date < date.today()

    def __str__(self):
        return f"{self.user.username} - {self.program.name}"


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True, help_text="Post Text")  
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def like_count(self):
        return self.likes.count()

    def __str__(self):
        return f"Post {self.id} by {self.user.username}"
