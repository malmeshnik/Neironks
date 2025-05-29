import cv2
import os
from ultralytics import YOLO
from django.conf import settings
from django.utils import timezone
from .models import DetectionResult, VideoUpload

YOLO_CLASS_NAMES = {
    0: 'car', 1: 'van', 2: '3-axle bus', 3: '2-axle bus', 4: 'car 1-axle trailer',
    5: 'car a 2-axle trailer', 6: 'truck 2-axle', 7: 'truck 3-axle', 8: 'truck 4-axle',
    9: '4-axle trailer', 10: '5-axle trailer', 11: '3-axle trailer', 12: '6-axle trailer',
    13: '3-axle saddle truck', 14: '4-axle saddle truck', 15: '5-axle saddle truck',
    16: '6-axle saddle truck', 17: 'trader', 18: 'trolleybus'
}

def process_video_with_yolo(video_upload_instance_id, model_path_str, class_names_dict):
    try:
        video_upload_instance = VideoUpload.objects.get(id=video_upload_instance_id)
        video_upload_instance.status = 'processing'
        video_upload_instance.save()

        model = YOLO(model_path_str)

        input_video_path = video_upload_instance.video_file.path
        cap = cv2.VideoCapture(input_video_path)

        if not cap.isOpened():
            raise Exception(f"Error opening video file: {input_video_path}")

        # Output video setup
        original_filename = os.path.basename(input_video_path)
        annotated_filename = f"{os.path.splitext(original_filename)[0]}_annotated.mp4"
        
        processed_videos_dir = os.path.join(settings.MEDIA_ROOT, 'processed_videos')
        if not os.path.exists(processed_videos_dir):
            os.makedirs(processed_videos_dir)
        
        output_video_path = os.path.join(processed_videos_dir, annotated_filename)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        frame_number = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1
            # Process frame with YOLO
            results = model(frame) # No resizing for now
            # results[0].plot() is a utility from Ultralytics that draws the detected boxes and labels onto the frame.
            annotated_frame = results[0].plot()
            out_writer.write(annotated_frame)

            # Data extraction
            # current_time_seconds is the timestamp of the current frame in seconds from the start of the video.
            current_time_seconds = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            frame_detections = {} # To store counts of each class in the current frame

            for box in results[0].boxes:
                try:
                    class_id = int(box.cls[0].item())
                    vehicle_class_name = class_names_dict.get(class_id, "unknown") # Use .get for safety
                    
                    if vehicle_class_name != "unknown":
                        frame_detections[vehicle_class_name] = frame_detections.get(vehicle_class_name, 0) + 1
                except Exception as e:
                    print(f"Error processing detection: {e}") # Log error and continue

            # Save DetectionResult for each detected class in the frame
            for vehicle_class, count in frame_detections.items():
                DetectionResult.objects.create(
                    video=video_upload_instance,
                    timestamp_in_video=current_time_seconds,
                    vehicle_class=vehicle_class,
                    count=count
                )
        
        cap.release()
        out_writer.release()

        cap.release()
        out_writer.release()

        # Aggregate data: After processing all frames and saving individual DetectionResult instances,
        # this section calculates the total count for each vehicle_class detected throughout the entire video.
        # These totals are then stored in the AggregatedData model.
        aggregated_results = {}
        all_detections_for_video = DetectionResult.objects.filter(video=video_upload_instance)
        for detection in all_detections_for_video: # Iterate over all per-frame detections for this video
            aggregated_results[detection.vehicle_class] = aggregated_results.get(detection.vehicle_class, 0) + detection.count
        
        from .models import AggregatedData # Moved import here to avoid circular if AggregatedData was in the same file
        for vehicle_class, total_count in aggregated_results.items():
            AggregatedData.objects.update_or_create(
                video=video_upload_instance,
                time_period_start=video_upload_instance.uploaded_at, # Using uploaded_at as per instruction
                vehicle_class=vehicle_class,
                defaults={'count': total_count}
            )

        video_upload_instance.processed_video_file.name = os.path.join('processed_videos', annotated_filename)
        video_upload_instance.status = 'completed'
        video_upload_instance.processed_at = timezone.now()
        video_upload_instance.save()

    except VideoUpload.DoesNotExist:
        print(f"VideoUpload instance with id {video_upload_instance_id} not found.")
        # No instance to update status for, or handle as appropriate
    except Exception as e:
        print(f"Error processing video {video_upload_instance_id}: {e}")
        if 'video_upload_instance' in locals() and VideoUpload.objects.filter(id=video_upload_instance_id).exists():
            video_upload_instance.status = 'failed'
            video_upload_instance.save()
    finally:
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        if 'out_writer' in locals():
            out_writer.release()
