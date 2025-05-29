from django.urls import path
# Removed: from . import views # views will be imported like views.ChartDataAPIView
from . import views # Keep this for existing views if you have views.main_dashboard_view etc.

urlpatterns = [
    path('', views.main_dashboard_view, name='main_dashboard'), 
    path('upload/', views.upload_video_view, name='upload_video'),
    path('stream/<int:video_id>/', views.stream_video_view, name='stream_video'),
    path('api/chart-data/', views.ChartDataAPIView.as_view(), name='api_chart_data'),
]
