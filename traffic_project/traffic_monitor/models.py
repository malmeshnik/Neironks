from django.db import models

class VideoUpload(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    video_file = models.FileField(upload_to='videos/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_video_file = models.FileField(upload_to='processed_videos/', null=True, blank=True)
    unique_car_count = models.IntegerField(default=0, help_text="DEPRECATED: Total number of unique cars tracked in the video. This is replaced by class-specific unique counts in AggregatedData.")

    def __str__(self):
        return self.video_file.name

class DetectionResult(models.Model):
    video = models.ForeignKey(VideoUpload, on_delete=models.CASCADE)
    timestamp_in_video = models.FloatField()
    vehicle_class = models.CharField(max_length=50)
    count = models.IntegerField()

    def __str__(self):
        return f"Detections for {self.video.video_file.name} at {self.timestamp_in_video}s: {self.count} {self.vehicle_class}(s)"

class AggregatedData(models.Model):
    video = models.ForeignKey(VideoUpload, on_delete=models.CASCADE)
    time_period_start = models.DateTimeField()
    vehicle_class = models.CharField(max_length=50)
    count = models.IntegerField(help_text="Stores the total count of unique objects of vehicle_class for the entire video.")

    class Meta:
        unique_together = ('video', 'time_period_start', 'vehicle_class')

    def __str__(self):
        return f"{self.count} {self.vehicle_class}(s) in {self.video.video_file.name} starting {self.time_period_start}"
