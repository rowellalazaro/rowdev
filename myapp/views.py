from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse  # ← ADDED (for zip_lookup)
from django.conf import settings  # ← ADDED (to read GOOGLE_MAPS_API_KEY)
import requests  # ← ADDED (to call the geocoding API)
from .forms import RegisterForm, PostForm, ProfileForm, UserUpdateForm
from .models import Post, Profile, DiaryEntry, PostImage, Notification, PDS, Education, WorkExperience, Skill, PostalCode  # ← ADDED PostalCode
from django.contrib.auth import logout as auth_logout
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from .models import PDS
from datetime import datetime  # ← ADDED


def pds_required(user):
    try:
        pds = user.pds
        return bool(pds.surname and pds.first_name)
    except:
        return False


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            group, created = Group.objects.get_or_create(name='Users')
            user.groups.add(group)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


@login_required
def home(request):
    if request.user.is_staff:
        return redirect('admin_page')
    if request.method == 'POST':
        content = request.POST.get('content')
        images = request.FILES.getlist('images')
        if content:
            post = Post.objects.create(
                content=content,
                author=request.user,
                title='Status Update'
            )
            for img in images:
                PostImage.objects.create(post=post, image=img)
        return redirect('home')
    posts = Post.objects.filter(author__is_active=True).order_by('-created_at')
    return render(request, 'home.html', {'posts': posts})


def admin_check(user):
    return user.groups.filter(name='Admins').exists()


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_page')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            auth_login(request, user)
            return redirect('admin_page')
        else:
            error = 'Invalid credentials or not an admin!'
    return render(request, 'admin_login.html', {'error': error})


def admin_page(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    from .models import UserRequest
    users = User.objects.all().order_by('-date_joined')
    requests_list = UserRequest.objects.all().order_by('-created_at')
    return render(request, 'admin.html', {'users': users, 'requests_list': requests_list})


def admin_delete_user(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    user = get_object_or_404(User, id=user_id)
    if user != request.user:
        user.delete()
    return redirect('admin_page')


def admin_toggle_user(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    user = get_object_or_404(User, id=user_id)
    if user != request.user:
        user.is_active = not user.is_active
        user.save()
    return redirect('admin_page')


def admin_delete_post(request, post_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect(request.META.get('HTTP_REFERER', 'admin_page'))


def admin_user_detail(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    u = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=u)
    posts = Post.objects.filter(author=u).order_by('-created_at')
    return render(request, 'admin_user_detail.html', {'u': u, 'profile': profile, 'posts': posts})


def admin_edit_user(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    u = get_object_or_404(User, id=user_id)
    error = None
    success = None
    if request.method == 'POST':
        new_username = request.POST.get('username', '').strip()
        new_email = request.POST.get('email', '').strip()
        if new_username and new_username != u.username:
            if User.objects.filter(username=new_username).exclude(id=u.id).exists():
                error = 'Username already taken.'
            else:
                u.username = new_username
        if new_email:
            u.email = new_email
        if not error:
            u.save()
            Notification.objects.create(
                user=u,
                message='Your account details have been updated by the admin.'
            )
            success = 'User updated successfully.'
    return render(request, 'admin_user_detail.html', {
        'u': u,
        'profile': Profile.objects.get_or_create(user=u)[0],
        'posts': Post.objects.filter(author=u).order_by('-created_at'),
        'edit_error': error,
        'edit_success': success,
    })


def admin_message_user(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    u = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            Notification.objects.create(user=u, message=message)
    return redirect('admin_user_detail', user_id=user_id)


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifs.filter(is_read=False).count()
    return render(request, 'notifications.html', {'notifs': notifs, 'unread_count': unread_count})


@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications')


@login_required
def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user_obj)
    posts = Post.objects.filter(author=user_obj).order_by('-created_at')
    return render(request, 'profile.html', {
        'profile_user': user_obj,
        'profile': profile,
        'posts': posts,
    })


@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_obj = profile_form.save(commit=False)
            if not request.FILES.get('profile_pic'):
                profile_obj.profile_pic = profile.profile_pic  # retain old pic
            profile_obj.save()
            return redirect('profile', username=request.user.username)
        else:
            print("Profile Form Errors:", profile_form.errors)
    else:
        profile_form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'profile_form': profile_form})


class PostListView(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'


class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'post_form.html'
    success_url = reverse_lazy('home')
    login_url = '/accounts/login/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        if not form.cleaned_data.get('title'):
            form.instance.title = "Status Update"
        response = super().form_valid(form)
        images = self.request.FILES.getlist('images')
        for img in images:
            PostImage.objects.create(post=self.object, image=img)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Post'
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post_form.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff

    def form_valid(self, form):
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Post'
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'post_confirm_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff


@login_required
def user_request(request):
    from .models import UserRequest
    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        message = request.POST.get('message')
        UserRequest.objects.create(
            user=request.user,
            request_type=request_type,
            current_value='',
            requested_value='',
            message=message
        )
        return redirect('user_request')
    my_requests = UserRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user_request.html', {'my_requests': my_requests})


@login_required
def files_view(request):
    posts = Post.objects.filter(author=request.user, image__isnull=False).exclude(image='').order_by('-created_at')
    return render(request, 'files.html', {'posts': posts})


@login_required
def settings_view(request):
    if request.method == 'POST':
        request.session['language'] = request.POST.get('language', 'en')
        request.session['theme'] = request.POST.get('theme', 'light')
        request.session.modified = True
        return redirect('home')
    return render(request, 'settings.html')


@login_required
def diary_view(request):
    entries = DiaryEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'diary.html', {'entries': entries})


@login_required
def diary_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        mood = request.POST.get('mood', '')
        if content:
            DiaryEntry.objects.create(
                user=request.user,
                title=title,
                content=content,
                mood=mood
            )
        return redirect('diary')
    return render(request, 'diary_form.html', {'action': 'New'})


@login_required
def diary_edit(request, pk):
    entry = get_object_or_404(DiaryEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.title = request.POST.get('title', '')
        entry.content = request.POST.get('content', '')
        entry.mood = request.POST.get('mood', '')
        entry.save()
        return redirect('diary')
    return render(request, 'diary_form.html', {'action': 'Edit', 'entry': entry})


@login_required
def diary_delete(request, pk):
    entry = get_object_or_404(DiaryEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
    return redirect('diary')


def admin_logout(request):
    auth_logout(request)
    return redirect('admin_login')


def admin_handle_request(request, request_id):
    from .models import UserRequest
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    req = get_object_or_404(UserRequest, id=request_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_note = request.POST.get('admin_note', '')
        if action == 'approve':
            req.status = 'approved'
            req.admin_note = admin_note
            req.save()
            u = req.user
            if req.request_type == 'username':
                u.username = req.requested_value
                u.save()
            elif req.request_type == 'bio':
                profile, _ = Profile.objects.get_or_create(user=u)
                profile.bio = req.requested_value
                profile.save()
            elif req.request_type == 'location':
                profile, _ = Profile.objects.get_or_create(user=u)
                profile.location = req.requested_value
                profile.save()
            elif req.request_type == 'birthday':
                profile, _ = Profile.objects.get_or_create(user=u)
                profile.birthday = req.requested_value
                profile.save()
            Notification.objects.create(
                user=u,
                message=f'Your request ({req.get_request_type_display()}) has been approved. {admin_note}'
            )
        elif action == 'reject':
            req.status = 'rejected'
            req.admin_note = admin_note
            req.save()
            Notification.objects.create(
                user=req.user,
                message=f'Your request ({req.get_request_type_display()}) has been rejected. {admin_note}'
            )
    return redirect('admin_page')


@login_required
def add_work(request):
    # ← FIXED: filter/create via pds (model has no 'user' field), and
    # only use fields that actually exist on WorkExperience.
    if request.method == 'POST':
        pds, _ = PDS.objects.get_or_create(user=request.user)
        if pds.work_experience.count() >= 3:
            return redirect('pds')
        position = request.POST.get('position', '')
        company = request.POST.get('company', '')
        date_from = request.POST.get('date_from') or None
        date_to = request.POST.get('date_to') or None
        is_current = request.POST.get('is_current') == 'on'
        WorkExperience.objects.create(
            pds=pds,
            position=position,
            company=company,
            date_from=date_from,
            date_to=None if is_current else date_to,
            is_current=is_current,
        )
    return redirect('pds')


@login_required
def delete_work(request, pk):
    pds = get_object_or_404(PDS, user=request.user)
    work = get_object_or_404(WorkExperience, pk=pk, pds=pds)
    if request.method == 'POST':
        work.delete()
    return redirect('pds')


@login_required
def add_skill(request):
    if request.method == 'POST':
        skill_name = request.POST.get('skill_name', '').strip()
        # ← FIXED: the form field is named "skill_category" (the id
        # "skill_category_hidden" is just the DOM id, not the POST key)
        skill_category = request.POST.get('skill_category', 'Other')
        if skill_name:
            pds, _ = PDS.objects.get_or_create(user=request.user)
            Skill.objects.create(pds=pds, name=skill_name, category=skill_category)
    return redirect('pds')


@login_required
def delete_skill(request, pk):
    pds = get_object_or_404(PDS, user=request.user)
    skill = get_object_or_404(Skill, pk=pk, pds=pds)
    if request.method == 'POST':
        skill.delete()
    return redirect('pds')


# ── NEW: geocoder fallback helper, used only when our own DB has no row yet ──
def _fetch_zip_from_geocoder(city_name, province_name=''):
    """
    Calls Google's Geocoding API and pulls the postal_code component out
    of the first result. Returns None on any failure (missing key, network
    error, no result, no postal_code component) so the caller can fall
    back gracefully instead of crashing the request.
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    if not api_key or not city_name:
        return None

    address = ', '.join(p for p in [city_name, province_name, 'Philippines'] if p)

    try:
        resp = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json',
            params={
                'address': address,
                'components': 'country:PH',
                'key': api_key,
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if data.get('status') != 'OK' or not data.get('results'):
        return None

    for component in data['results'][0].get('address_components', []):
        if 'postal_code' in component.get('types', []):
            return component.get('long_name')
    return None


# ── UPDATED: now DB-first, with geocoder fallback + auto-cache ──
def zip_lookup(request):
    """
    GET /pds/zip-lookup/?city_code=031403000&city_name=Malolos&province_name=Bulacan

    Lookup order:
      1. Our own PostalCode table (free, instant, correctable in admin).
      2. If not found: Google Geocoding API (needs GOOGLE_MAPS_API_KEY
         in settings.py). On a hit, the result is cached into PostalCode
         so the next lookup for that city is a free DB hit, not another
         paid API call.

    Returns: {"zip": "3000", "source": "db"} / {"zip": "3000", "source": "geocoder"}
             {"zip": null, "source": null} if nothing was found anywhere.
    """
    city_code = (request.GET.get('city_code') or '').strip()
    city_name = (request.GET.get('city_name') or '').strip()
    province_name = (request.GET.get('province_name') or '').strip()  # ← ADDED, optional but improves geocoder accuracy

    # 1. Try our own DB first
    match = None
    if city_code:
        match = PostalCode.objects.filter(psgc_city_code=city_code).first()
    elif city_name:
        match = PostalCode.objects.filter(city_name__iexact=city_name).first()

    if match:
        return JsonResponse({'zip': match.zip_code, 'source': 'db'})

    # 2. Not in our DB yet — fall back to the geocoding API
    zip_code = _fetch_zip_from_geocoder(city_name, province_name)
    if zip_code:
        # Cache it for next time, but only if we have a stable key (city_code)
        # to cache it under — without one we'd risk creating duplicate/wrong
        # rows keyed loosely on name alone.
        if city_code:
            PostalCode.objects.update_or_create(
                psgc_city_code=city_code,
                defaults={
                    'city_name': city_name,
                    'province_name': province_name,
                    'zip_code': zip_code,
                },
            )
        return JsonResponse({'zip': zip_code, 'source': 'geocoder'})

    # 3. Nothing found anywhere
    return JsonResponse({'zip': None, 'source': None})


@login_required
def pds_view(request):
    pds, created = PDS.objects.get_or_create(user=request.user)

    education = {level: None for level in ['elementary', 'secondary', 'college', 'vocational']}
    for edu in pds.education.all():
        education[edu.level] = edu
    work_list = pds.work_experience.all().order_by('-date_from')
    skills = pds.skills.all()

    # ← ADDED: year choices for education dropdowns
    year_choices = list(range(datetime.now().year, 1979, -1))

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── FIX: the main PDS form (personal info + address + education)
        # submits action="save_all", but this branch didn't exist before,
        # so nothing was ever saved and the page reloaded with blank/old data.
        if action in ('save_all', 'save_personal'):
            pds.surname = request.POST.get('surname', '')
            pds.first_name = request.POST.get('first_name', '')
            pds.middle_name = request.POST.get('middle_name', '')
            pds.name_extension = request.POST.get('name_extension', '')
            pds.age = request.POST.get('age', '')
            pds.date_of_birth = request.POST.get('date_of_birth') or None
            pds.place_of_birth = request.POST.get('place_of_birth', '')
            pds.sex = request.POST.get('sex', '')
            pds.civil_status = request.POST.get('civil_status', '')
            pds.height = request.POST.get('height', '')
            pds.weight = request.POST.get('weight', '')
            pds.blood_type = request.POST.get('blood_type', '')
            pds.citizenship = request.POST.get('citizenship', '')
            pds.res_house_no = request.POST.get('res_house_no', '')
            pds.res_street = request.POST.get('res_street', '')
            pds.res_subdivision = request.POST.get('res_subdivision', '')
            pds.res_barangay = request.POST.get('res_barangay', '')
            pds.res_city = request.POST.get('res_city', '')
            pds.res_province = request.POST.get('res_province', '')
            pds.res_zip = request.POST.get('res_zip', '')
            pds.perm_house_no = request.POST.get('perm_house_no', '')
            pds.perm_street = request.POST.get('perm_street', '')
            pds.perm_subdivision = request.POST.get('perm_subdivision', '')
            pds.perm_barangay = request.POST.get('perm_barangay', '')
            pds.perm_city = request.POST.get('perm_city', '')
            pds.perm_province = request.POST.get('perm_province', '')
            pds.perm_zip = request.POST.get('perm_zip', '')
            pds.telephone = request.POST.get('telephone', '')
            pds.mobile = request.POST.get('mobile', '')
            pds.email = request.POST.get('email', '')
            pds.save()

        if action in ('save_all', 'save_education'):
            # ← UPDATED: now also saves edu_status per level
            for level in ['elementary', 'secondary', 'college', 'vocational']:
                school = request.POST.get(f'{level}_school', '')
                course = request.POST.get(f'{level}_course', '')
                year = request.POST.get(f'{level}_year', '')
                status = request.POST.get(f'{level}_status', '')  # ← ADDED
                edu, _ = Education.objects.get_or_create(pds=pds, level=level)
                edu.school = school
                edu.course = course
                edu.year_graduated = year
                edu.edu_status = status  # ← ADDED
                edu.save()

        # ── FIX: these forms in pds.html have no action="" attribute, so
        # they post back to this same view (not the separate add_work /
        # delete_work / add_skill / delete_skill views). Without these
        # branches the buttons silently did nothing.
        elif action == 'add_work':
            if pds.work_experience.count() < 3:
                is_current = request.POST.get('is_current') == 'on'
                WorkExperience.objects.create(
                    pds=pds,
                    company=request.POST.get('company', ''),
                    position=request.POST.get('position', ''),
                    date_from=request.POST.get('date_from') or None,
                    date_to=None if is_current else (request.POST.get('date_to') or None),
                    is_current=is_current,
                )

        elif action == 'delete_work':
            WorkExperience.objects.filter(pds=pds, id=request.POST.get('work_id')).delete()

        elif action == 'add_skill':
            skill_name = request.POST.get('skill_name', '').strip()
            skill_category = request.POST.get('skill_category', 'Other')
            if skill_name:
                Skill.objects.create(pds=pds, name=skill_name, category=skill_category)

        elif action == 'delete_skill':
            Skill.objects.filter(pds=pds, id=request.POST.get('skill_id')).delete()

        return redirect('pds')

    return render(request, 'pds.html', {
        'pds': pds,
        'education': education,
        'work_list': work_list,
        'skills': skills,
        'year_choices': year_choices,  # ← ADDED
    })


def admin_pds_list(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    from django.db.models import Q
    sort = request.GET.get('sort', 'username')
    search = request.GET.get('search', '')
    pds_qs = PDS.objects.select_related('user').all()
    if search:
        pds_qs = pds_qs.filter(
            Q(user__username__icontains=search) |
            Q(surname__icontains=search) |
            Q(first_name__icontains=search)
        )

    # ← Sorting is done in Python (not the DB) because 'age' is a CharField,
    # so a plain .order_by('age') would sort it as text ("10" before "9").
    pds_list = list(pds_qs)

    def text_key(value):
        return (value or '').strip().lower()

    def age_key(p):
        try:
            return (0, int(p.age))
        except (TypeError, ValueError):
            return (1, 0)  # blank/non-numeric ages sort last

    def birthday_key(p):
        return (p.date_of_birth is None, p.date_of_birth)

    sort_map = {
        'first_name': lambda p: text_key(p.first_name),
        'last_name': lambda p: text_key(p.surname),
        'surname': lambda p: text_key(p.surname),  # kept for backward compatibility
        'age': age_key,
        'birthday': birthday_key,
        'province': lambda p: text_key(p.res_province),
        'municipality': lambda p: text_key(p.res_city),
        'barangay': lambda p: text_key(p.res_barangay),
        'sex': lambda p: text_key(p.sex),
        'username': lambda p: text_key(p.user.username),
        'updated': lambda p: p.updated_at,
    }

    key_func = sort_map.get(sort, sort_map['username'])
    pds_list.sort(key=key_func, reverse=(sort == 'updated'))

    return render(request, 'admin_pds.html', {'pds_list': pds_list, 'sort': sort, 'search': search})


def admin_pds_detail(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')

    u = get_object_or_404(User, id=user_id)
    pds, created = PDS.objects.get_or_create(user=u)

    education = {level: None for level in ['elementary', 'secondary', 'college', 'vocational']}
    for edu in pds.education.all():
        education[edu.level] = edu

    work_list = pds.work_experience.all().order_by('-date_from')
    skills = pds.skills.all()

    return render(request, 'admin_pds_detail.html', {
        'u': u,
        'pds': pds,
        'education': education,
        'work_list': work_list,
        'skills': skills,
    })