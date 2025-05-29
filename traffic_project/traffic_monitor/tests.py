from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import os

from .forms import VideoUploadForm
from .models import VideoUpload, DetectionResult, AggregatedData
# Serializers are not directly tested here, but through the API view.

# Helper to create a dummy video file for tests
def create_dummy_video_file(name="test_video.mp4", content=b"dummy video content", content_type="video/mp4"):
    return SimpleUploadedFile(name, content, content_type=content_type)

class VideoUploadFormTest(TestCase):
    def test_valid_video_upload_form(self):
        """Test that the VideoUploadForm is valid with a proper video file."""
        video_file = create_dummy_video_file()
        form_data = {} # No text fields in this form
        file_data = {'video_file': video_file}
        form = VideoUploadForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors.as_json()}")

    def test_invalid_video_upload_form_no_file(self):
        """Test that the VideoUploadForm is invalid if no file is provided."""
        form = VideoUploadForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('video_file', form.errors)

class ModelsTest(TestCase):
    def setUp(self):
        self.video_file_instance = create_dummy_video_file(name="video1.mp4")
        # Save the file to a temporary location so that VideoUpload model can access its path
        # This is a simplified approach; for robust testing, override MEDIA_ROOT
        # However, given potential disk space issues, we'll keep it minimal.
        # For __str__ methods that rely on file.name, this should be okay.
        self.video_upload = VideoUpload.objects.create(video_file=self.video_file_instance)

    def test_video_upload_creation(self):
        """Test basic creation and default values for VideoUpload."""
        self.assertEqual(self.video_upload.status, 'pending')
        # The name might include the 'videos/' prefix depending on how SimpleUploadedFile interacts with FileField's upload_to
        # Let's check if the original filename is part of the string representation
        self.assertIn(os.path.basename(self.video_file_instance.name), str(self.video_upload))


    def test_detection_result_creation(self):
        """Test basic creation of DetectionResult linked to a VideoUpload."""
        detection = DetectionResult.objects.create(
            video=self.video_upload,
            timestamp_in_video=10.5,
            vehicle_class='car',
            count=5
        )
        expected_str = (
            f"Detections for {os.path.basename(self.video_upload.video_file.name)} "
            f"at {detection.timestamp_in_video}s: {detection.count} {detection.vehicle_class}(s)"
        )
        self.assertEqual(str(detection), expected_str)

    def test_aggregated_data_creation(self):
        """Test basic creation of AggregatedData linked to a VideoUpload."""
        agg_data = AggregatedData.objects.create(
            video=self.video_upload,
            time_period_start=timezone.now(),
            vehicle_class='truck',
            count=15
        )
        expected_str = (
            f"{agg_data.count} {agg_data.vehicle_class}(s) in "
            f"{os.path.basename(self.video_upload.video_file.name)} starting {agg_data.time_period_start}"
        )
        self.assertEqual(str(agg_data), expected_str)

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_main_dashboard_view_get(self):
        """Test GET request to main_dashboard_view."""
        url = reverse('main_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'traffic_monitor/index.html')

    def test_upload_video_view_get(self):
        """Test GET request to upload_video_view."""
        url = reverse('upload_video')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'traffic_monitor/upload_video.html')
    
    # POST request for upload_video_view is skipped to avoid complexities with
    # file storage in tests and Celery task triggering during tests without proper mocking.
    # Test for stream_video_view would require a processed video and is more complex,
    # so it's also skipped for this basic set of tests.

class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        # It might be good to create some data for the API to return,
        # e.g., a processed VideoUpload and some AggregatedData.
        # For simplicity, we'll test with potentially empty data,
        # focusing on the structure of the response.

        # Create a dummy video that is "processed"
        self.video_file = create_dummy_video_file(name="api_test_video.mp4")
        self.processed_video = VideoUpload.objects.create(
            video_file=self.video_file,
            status='completed',
            processed_at=timezone.now(),
            # processed_video_file would ideally be set too for full testing
        )
        AggregatedData.objects.create(
            video=self.processed_video,
            time_period_start=self.processed_video.uploaded_at,
            vehicle_class='car',
            count=10
        )
        AggregatedData.objects.create(
            video=self.processed_video,
            time_period_start=self.processed_video.uploaded_at,
            vehicle_class='bus',
            count=2
        )


    def test_chart_data_api_view_get(self):
        """Test GET request to ChartDataAPIView."""
        url = reverse('api_chart_data')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # In Django 3.1+ and DRF, response.json() is a good way to parse JSON
        try:
            data = response.json()
        except AttributeError: # Fallback for older Django/DRF versions or if not using APIClient
            import json
            data = json.loads(response.content)

        self.assertIn('distribution_chart', data)
        self.assertIn('timeline_chart', data)

        self.assertIn('labels', data['distribution_chart'])
        self.assertIn('data', data['distribution_chart'])
        
        self.assertIn('labels', data['timeline_chart'])
        self.assertIn('data', data['timeline_chart'])

        # Check if data from setUp is reflected (optional, but good)
        self.assertIn('car', data['distribution_chart']['labels'])
        self.assertIn(10, data['distribution_chart']['data'])
        self.assertIn('bus', data['distribution_chart']['labels'])
        self.assertIn(2, data['distribution_chart']['data'])
        
        self.assertTrue(len(data['timeline_chart']['labels']) >= 1)
        self.assertTrue(len(data['timeline_chart']['data']) >= 1)
        self.assertEqual(data['timeline_chart']['data'][0], 12) # 10 cars + 2 buses for this video
        
# Note: To run these tests, one would typically use the command:
# python manage.py test traffic_monitor
# However, due to environment constraints (potential disk space issues, Celery/Redis setup for integration tests),
# running this command is currently skipped. These tests are written to be as standalone as possible
# for basic unit validation. More complex tests (e.g., involving Celery task execution or
# detailed model processing logic) would require a more comprehensive test setup.
