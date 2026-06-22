from datetime import date

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
    RELIGION_CHOICES = [
        ('catholic', 'Roman Catholic'),
        ('protestant', 'Protestant'),
        ('iglesia_ni_cristo', 'Iglesia ni Cristo'),
        ('islam', 'Islam'),
        ('other', 'Other'),
        ('none', 'Prefer not to say'),
    ]

    # Maps province name -> region label, used for the `region` property below.
    # Extend this as you cover more provinces.
    PROVINCE_TO_REGION = {
        'Bulacan': 'Region III - Central Luzon',
        'Pampanga': 'Region III - Central Luzon',
        'Nueva Ecija': 'Region III - Central Luzon',
        'Tarlac': 'Region III - Central Luzon',
        'Zambales': 'Region III - Central Luzon',
        'Bataan': 'Region III - Central Luzon',
        'Aurora': 'Region III - Central Luzon',
        'Metro Manila': 'NCR - National Capital Region',
        'Manila': 'NCR - National Capital Region',
        'Cavite': 'Region IV-A - CALABARZON',
        'Laguna': 'Region IV-A - CALABARZON',
        'Batangas': 'Region IV-A - CALABARZON',
        'Rizal': 'Region IV-A - CALABARZON',
        'Quezon': 'Region IV-A - CALABARZON',
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pds')

    # Personal Info
    surname = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    name_extension = models.CharField(max_length=20, blank=True)
    age = models.CharField(max_length=5, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=200, blank=True)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES, blank=True, db_index=True)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES, blank=True, db_index=True)
    height = models.CharField(max_length=20, blank=True)
    weight = models.CharField(max_length=20, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    blood_type = models.CharField(max_length=5, blank=True, db_index=True)
    citizenship = models.CharField(max_length=20, choices=CITIZENSHIP_CHOICES, blank=True, db_index=True)
    religion = models.CharField(max_length=30, choices=RELIGION_CHOICES, blank=True, db_index=True)

    # Residential Address
    res_house_no = models.CharField(max_length=100, blank=True)
    res_street = models.CharField(max_length=100, blank=True)
    res_subdivision = models.CharField(max_length=100, blank=True)
    res_barangay = models.CharField(max_length=100, blank=True)
    res_city = models.CharField(max_length=100, blank=True, db_index=True)
    res_province = models.CharField(max_length=100, blank=True, db_index=True)
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

    def save(self, *args, **kwargs):
        # Normalize free-text location fields so "bulacan", "Bulacan ", "BULACAN"
        # don't fragment into separate rows in stats breakdowns.
        for field in ['res_province', 'res_city', 'res_barangay', 'perm_province', 'perm_city', 'perm_barangay']:
            value = getattr(self, field)
            if value:
                setattr(self, field, value.strip().title())
        super().save(*args, **kwargs)

    @property
    def computed_age(self):
        """Age derived from date_of_birth, used instead of the free-text `age` field for stats."""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def region(self):
        """Region derived from res_province, kept in sync automatically rather than typed separately."""
        return self.PROVINCE_TO_REGION.get(self.res_province, 'Unspecified')

    @property
    def highest_education_level(self):
        """Single highest education level for this respondent, or None if no records."""
        levels = self.education.values_list('level', flat=True)
        if not levels:
            return None
        return max(levels, key=lambda lvl: Education.LEVEL_RANK.get(lvl, 0))

    def __str__(self):
        return f"PDS of {self.user.username}"


class Education(models.Model):
    LEVEL_CHOICES = [
        ('elementary', 'Elementary'),
        ('secondary', 'Secondary'),
        ('vocational', 'Vocational'),
        ('college', 'College'),
    ]
    LEVEL_RANK = {'elementary': 1, 'secondary': 2, 'vocational': 3, 'college': 4}
    EDU_STATUS_CHOICES = [
        ('graduated', 'Graduated'),
        ('undergraduate', 'Undergraduate'),
        ('ongoing', 'Ongoing'),
    ]
    pds = models.ForeignKey(PDS, on_delete=models.CASCADE, related_name='education')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, db_index=True)
    school = models.CharField(max_length=200, blank=True)
    course = models.CharField(max_length=200, blank=True)
    edu_status = models.CharField(max_length=20, choices=EDU_STATUS_CHOICES, blank=True)
    year_graduated = models.CharField(max_length=10, blank=True)

    @property
    def level_rank(self):
        return self.LEVEL_RANK.get(self.level, 0)

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
        ('hobby', 'Hobby/Interest'),
        ('other', 'Other'),
    ]
    pds = models.ForeignKey(PDS, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES, default='other', db_index=True)

    def __str__(self):
        return self.name


class Recognition(models.Model):
    """Non-academic distinctions / recognitions (awards, citations, etc.)."""
    pds = models.ForeignKey(PDS, on_delete=models.CASCADE, related_name='recognitions')
    title = models.CharField(max_length=200)
    issuing_body = models.CharField(max_length=200, blank=True)
    year = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.title