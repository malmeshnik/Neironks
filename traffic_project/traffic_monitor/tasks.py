from celery import shared_task
from .yolo_processor import process_video_with_yolo, YOLO_CLASS_NAMES
from django.conf import settings
import os

@shared_task
def process_video_task(video_upload_id):
    # Construct the full path to the YOLO model file (`best.pt`).
    # `settings.BASE_DIR` points to the root directory of the Django project (where manage.py is).
    # This assumes `best.pt` is placed in the project root.
    model_path = os.path.join(settings.BASE_DIR, 'best.pt')
    try:
        # It's better to pass IDs and simple data types (like strings for paths) to Celery tasks
        # rather than complex objects like model instances.
        # The `process_video_with_yolo` function is designed to fetch the VideoUpload instance using its ID.
        process_video_with_yolo(video_upload_id, str(model_path), YOLO_CLASS_NAMES)
    except Exception as e:
        # Log the exception or handle it appropriately
        # You might want to update the VideoUpload status to 'failed' here
        # if process_video_with_yolo doesn't robustly handle its own errors
        # regarding model status updates.
        print(f"Error processing video ID {video_upload_id}: {e}")
        # Optionally, re-raise or handle to ensure task failure is noted by Celery
        # For now, we'll let yolo_processor handle status updates on its own.
        # If critical errors prevent yolo_processor from even starting,
        # the VideoUpload status might remain 'processing' or 'pending'.
        # A more robust solution would involve a try-except in this task
        # that explicitly sets status to 'failed' if process_video_with_yolo crashes badly.
        raise # Re-raise the exception to mark the task as failed in Celery
        
# Note: The yolo_processor.py's process_video_with_yolo function is expected
# to handle its own try/except blocks for internal errors and update the
# VideoUpload model's status accordingly ('completed' or 'failed').
# This task's try/except is mainly for issues invoking process_video_with_yolo
# itself or for critical, unhandled exceptions bubbling up from it.
