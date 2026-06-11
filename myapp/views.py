from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import RegisterForm, PostForm, ProfileForm, UserUpdateForm
from .models import Post, Profile, DiaryEntry
from django.contrib.auth import logout as auth_logout


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
        image = request.FILES.get('image')
        if content:
            Post.objects.create(
                content=content,
                image=image,
                author=request.user,
                title='Status Update'
            )
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
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile', username=request.user.username)
        else:
            print("--- Form Validation Failed ---")
            print("User Form Errors:", user_form.errors)
            print("Profile Form Errors:", profile_form.errors)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


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
        return super().form_valid(form)

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
        elif action == 'reject':
            req.status = 'rejected'
            req.admin_note = admin_note
            req.save()
    return redirect('admin_page')