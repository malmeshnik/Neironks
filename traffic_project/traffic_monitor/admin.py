from django.contrib import admin
from .models import VideoUpload, DetectionResult, AggregatedData


# Register your models here.
@admin.register(VideoUpload)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'video_file', 'status', 'uploaded_at', 'processed_at')
    search_fields = ('video_file',)
    list_filter = ('uploaded_at',)

@admin.register(DetectionResult)
class DetectionResultAdmin(admin.ModelAdmin):
    list_display = ('video', 'timestamp_in_video', 'vehicle_class', 'count')
    search_fields = ('video__title', 'vehicle_class')
    list_filter = ('vehicle_class',)

@admin.register(AggregatedData)
class AggregatedDataAdmin(admin.ModelAdmin):
    list_display = ('video', 'time_period_start', 'vehicle_class', 'count')
    search_fields = ('video__title', 'vehicle_class')
    list_filter = ('vehicle_class',)

