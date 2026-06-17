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


class PDS(models.Model):
    SEX_CHOICES = [('male', 'Male'), ('female', 'Female')]
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
        ('other', 'Other'),
    ]
    CITIZENSHIP_CHOICES = [('filipino', 'Filipino'), ('dual', 'Dual Citizenship')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pds')

    # Personal Info
    surname = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    name_extension = models.CharField(max_length=20, blank=True)
    age = models.CharField(max_length=5, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=200, blank=True)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES, blank=True)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES, blank=True)
    height = models.CharField(max_length=20, blank=True)
    weight = models.CharField(max_length=20, blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    citizenship = models.CharField(max_length=20, choices=CITIZENSHIP_CHOICES, blank=True)

    # Residential Address
    res_house_no = models.CharField(max_length=100, blank=True)
    res_street = models.CharField(max_length=100, blank=True)
    res_subdivision = models.CharField(max_length=100, blank=True)
    res_barangay = models.CharField(max_length=100, blank=True)
    res_city = models.CharField(max_length=100, blank=True)
    res_province = models.CharField(max_length=100, blank=True)
    res_zip = models.CharField(max_length=10, blank=True)

    # Permanent Address
    perm_house_no = models.CharField(max_length=100, blank=True)
    perm_street = models.CharField(max_length=100, blank=True)
    perm_subdivision = models.CharField(max_length=100, blank=True)
    perm_barangay = models.CharField(max_length=100, blank=True)
    perm_city = models.CharField(max_length=100, blank=True)
    perm_province = models.CharField(max_length=100, blank=True)
    perm_zip = models.CharField(max_length=10, blank=True)

    telephone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=100, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PDS of {self.user.username}"


class Education(models.Model):
    LEVEL_CHOICES = [
        ('elementary', 'Elementary'),
        ('secondary', 'Secondary'),
        ('vocational', 'Vocational'),
        ('college', 'College'),
    ]
    EDU_STATUS_CHOICES = [
        ('graduated', 'Graduated'),
        ('undergraduate', 'Undergraduate'),
        ('ongoing', 'Ongoing'),
    ]
    pds = models.ForeignKey(PDS, on_delete=models.CASCADE, related_name='education')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    school = models.CharField(max_length=200, blank=True)
    course = models.CharField(max_length=200, blank=True)
    edu_status = models.CharField(max_length=20, choices=EDU_STATUS_CHOICES, blank=True)
    year_graduated = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.level} - {self.school}"


class WorkExperience(models.Model):
    pds = models.ForeignKey(PDS, on_delete=models.CASCADE, related_name='work_experience')
    company = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=200, blank=True)
    date_from = models.DateField(blank=True, null=True)
    date_to = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.position} at {self.company}"


class Skill(models.Model):
    SKILL_CATEGORIES = [
        ('technical', 'Technical'),
        ('soft', 'Soft Skills'),
        ('language', 'Language'),
        ('tools', 'Tools & Software'),
        ('professional', 'Professional'),
        ('other', 'Other'),
    ]
    pds = models.ForeignKey(PDS, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES, default='other')

    def __str__(self):
        return self.name
