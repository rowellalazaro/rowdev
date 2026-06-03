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
    path('profile/edit/', views.edit_profile, name='edit-profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),

    # Admin URLs
    path('rowdev-admin/', views.admin_login, name='admin_login'),
    path('rowdev-admin/dashboard/', views.admin_page, name='admin_page'),
    path('rowdev-admin/user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('rowdev-admin/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('rowdev-admin/toggle/<int:user_id>/', views.admin_toggle_user, name='admin_toggle_user'),
    path('rowdev-admin/post/delete/<int:post_id>/', views.admin_delete_post, name='admin_delete_post'),
    path('rowdev-admin/logout/', views.admin_logout, name='admin_logout'),
    path('settings/request/', views.user_request, name='user_request'),
    path('rowdev-admin/request/<int:request_id>/', views.admin_handle_request, name='admin_handle_request'),
]