from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Post(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or "Status Update"


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='extra_images')
    image = models.ImageField(upload_to='post_images/')

    def __str__(self):
        return f"Image for {self.post}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class UserRequest(models.Model):
    REQUEST_TYPES = [
        ('bug', 'Bug Report'),
        ('error', 'Error / Something Not Working'),
        ('suggestion', 'Suggestion / Feature Request'),
        ('account', 'Account Concern'),
        ('content', 'Content Concern'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    current_value = models.CharField(max_length=200, blank=True, null=True)
    requested_value = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.request_type} - {self.status}"


class DiaryEntry(models.Model):
    MOOD_CHOICES = [
        ('happy', '😊 Happy'),
        ('sad', '😢 Sad'),
        ('angry', '😠 Angry'),
        ('anxious', '😰 Anxious'),
        ('calm', '😌 Calm'),
        ('excited', '🤩 Excited'),
        ('tired', '😴 Tired'),
        ('neutral', '😐 Neutral'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Entry'} - {self.created_at.date()}"

    class Meta:
        ordering = ['-created_at']


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

    class Meta:
        ordering = ['-created_at']