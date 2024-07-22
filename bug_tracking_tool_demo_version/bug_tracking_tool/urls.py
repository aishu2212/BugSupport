
from django.contrib import admin
from django.urls import path, include
from accounts import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from accounts import bug_restapi

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('developer/create/', views.create_developer, name='create_developer'),
    path('notifications', views.notifications, name='notifications'),
    path('tester/create/', views.create_tester, name='create_tester'),
    path('signup/', views.user_signup, name='user_signup'),
    path('login/', views.user_login, name='user_login'),
    path('mark_notifications_as_read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),
    path('fetch_new_notifications/', views.fetch_new_notifications, name='fetch_new_notifications'),
    path('notification_count/', views.notification_count, name='notification_count'),
    path('create/', views.bug_create, name='bug_create'),
    path('bug_detail/<int:bug_id>/', views.bug_detail, name='bug_detail'),
    path('bug_dashboard/', views.bug_dashboard, name='bug_dashboard'),
     path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/profile/', views.profile_view, name='user_profile'),
    path('bugs/<int:bug_id>/export-pdf/', views.export_bug_details_to_pdf, name='export_bug_to_pdf'),
    path('analytics/', views.bug_analytics, name='bug_analytics'),
    path('similar_bug_popup/', views.similar_bug_popup, name='similar_bug_popup'),
    path('bugs/<int:bug_id>/', bug_restapi.BugDetailView.as_view(), name='bug_detail_api'),
    path('fetch_user/<int:user_id>/', bug_restapi.FetchUserDetailsView.as_view(), name='fetch_user_details'),
    path('notifications/<int:user_id>/', bug_restapi.NotificationDetailView.as_view(), name='notification_detail'),
    path('bugs/<int:bug_id>/similar/', bug_restapi.SimilarBugView.as_view(), name='similar_bugs'),
    path('bug_analytics_api/<int:user_id>/', bug_restapi.BugAnalyticsView.as_view(), name='bug_analytics_api'),
    path('bug_filter/<int:user_id>/', bug_restapi.BugFilterView.as_view(), name='bug_filter'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

