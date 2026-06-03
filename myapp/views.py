from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import RegisterForm, PostForm, ProfileForm, UserUpdateForm
from .models import Post, Profile


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            group, created = Group.objects.get_or_create(name='Users')
            user.groups.add(group)
            messages.success(request, "Account created successfully!")
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
            messages.success(request, "Posted successfully!")
        return redirect('home')

    posts = Post.objects.all().order_by('-created_at')
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
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin.html', {'users': users})


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
            messages.success(request, "Profile updated successfully!")
            return redirect('profile', username=request.user.username)
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
        messages.success(self.request, "Post created successfully!")
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
        messages.success(self.request, "Post updated successfully!")
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
def settings_view(request):
    if request.method == 'POST':
        request.session['language'] = request.POST.get('language', 'en')
        request.session['theme'] = request.POST.get('theme', 'light')
        request.session.modified = True
        messages.success(request, 'Settings saved!')
        return redirect('home')
    return render(request, 'settings.html')