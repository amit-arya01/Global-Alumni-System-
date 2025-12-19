# alumni_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.alumni_dashboard, name='alumni_dashboard'),
    path('change-password/', views.change_password, name='change_password'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('alumni-gallery/', views.alumni_gallery, name='alumni_gallery'),
    path('notifications/', views.notifications, name='notifications'),
    path('feedback/', views.submit_feedback, name='feedback'),
    path('resolve-feedback/<int:feedback_id>/', views.resolve_feedback, name='resolve_feedback'),
    path('toggle-alumni/<int:alumni_id>/', views.toggle_alumni_status, name='toggle_alumni_status'),
  
    path('manage/events/', views.admin_events, name='admin_events'),
    path('manage/events/create/', views.create_event, name='create_event'),
    path('manage/events/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('manage/events/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('events/', views.view_events, name='view_events'),
    # New URLs for connection functionality
    path('browse_alumni/', views.browse_alumni, name='browse_alumni'),
    path('send_connection_request/<int:receiver_id>/', views.send_connection_request, name='send_connection_request'),
    path('respond_connection_request/<int:connection_id>/<str:action>/', views.respond_connection_request, name='respond_connection_request'),
    # Post-related URLs
    path('posts/create/', views.create_post, name='create_post'),
    path('posts/', views.view_posts, name='view_posts'),
    path('posts/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('posts/edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('alumni/profile/<int:alumni_id>/', views.view_alumni_profile, name='view_alumni_profile'),
    path('alumni/edit-profile/', views.edit_profile, name='edit_profile'),
    path('inbox/', views.inbox, name='inbox'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('send-message/', views.send_message, name='send_message'),
    path('start-chat/<int:alumni_id>/', views.start_chat, name='start_chat'),
    path('clear-chat/<int:room_id>/', views.clear_chat, name='clear_chat'),
]