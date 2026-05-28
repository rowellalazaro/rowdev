from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('posts/', views.PostListView.as_view(), name='post-list'),
    path('post/create/', views.PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post-edit'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post-delete'),
    path('admin-page/', views.admin_page, name='admin_page'),
    path('profile/edit/', views.edit_profile, name='edit-profile'), 
    path('profile/<str:username>/', views.profile_view, name='profile'),  
]