from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse, Http404
from .forms import VideoUploadForm
from .models import VideoUpload, AggregatedData, DetectionResult
from .tasks import process_video_task
from django.db.models import Sum, F, FloatField
# from django.db.models.functions import Cast # Not used in the current implementation of graph_data_query

def main_dashboard_view(request):
    latest_processed_video = VideoUpload.objects.filter(status='completed').order_by('-processed_at').first()
    overall_stats = {'total_vehicles': 0} # Default
    vehicle_breakdown = None

    if latest_processed_video:
        # Updated overall_stats to fetch unique car count
        car_data = AggregatedData.objects.filter(video=latest_processed_video, vehicle_class='car').first()
        if car_data:
            overall_stats['total_vehicles'] = car_data.count

        vehicle_breakdown = AggregatedData.objects.filter(video=latest_processed_video).order_by('vehicle_class')

    # Initialize context with new timeline structure
    context = {
        'latest_video': latest_processed_video,
        'overall_stats': overall_stats,
        'vehicle_breakdown': vehicle_breakdown,
        'distribution_labels': [],
        'distribution_data': [],
        'timeline_labels': [], # Will be populated by new logic
        'timeline_data': [],   # Will be populated by new logic
    }

    if latest_processed_video and vehicle_breakdown:
        context['distribution_labels'] = [item.vehicle_class for item in vehicle_breakdown]
        context['distribution_data'] = [item.count for item in vehicle_breakdown]

    # New "Traffic Over Time" chart data logic for the latest_processed_video
    new_timeline_labels = []
    new_timeline_data = []
    if latest_processed_video:
        detections_over_time = DetectionResult.objects.filter(video=latest_processed_video).order_by('timestamp_in_video')

        # Placeholder logic (cumulative sum of objects detected per timestamp):
        # This is NOT "unique cumulative" but sums DetectionResult.count over time for the video.
        temp_timeline_data = {} # timestamp: count_at_timestamp
        for dr in detections_over_time:
            ts = dr.timestamp_in_video
            temp_timeline_data[ts] = temp_timeline_data.get(ts, 0) + dr.count # Sum counts if multiple classes at same ts

        sorted_timestamps = sorted(temp_timeline_data.keys())
        running_total = 0
        for ts in sorted_timestamps:
            running_total += temp_timeline_data[ts]
            new_timeline_labels.append(f"{ts:.2f}s") # Format timestamp
            new_timeline_data.append(running_total)

    context['timeline_labels'] = new_timeline_labels
    context['timeline_data'] = new_timeline_data
    
    return render(request, 'traffic_monitor/index.html', context)

def upload_video_view(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            new_video = form.save()
            # Set status to pending explicitly if not default, or rely on default
            # new_video.status = 'pending' 
            # new_video.save()
            process_video_task.delay(new_video.id)
            return redirect('/') 
    else:
        form = VideoUploadForm()
    return render(request, 'traffic_monitor/upload_video.html', {'form': form})

def stream_video_view(request, video_id):
    video_upload = get_object_or_404(VideoUpload, id=video_id, status='completed')
    if not video_upload.processed_video_file:
        raise Http404("Processed video file not found.")

    try:
        # Ensure the file path is correct and accessible
        file_path = video_upload.processed_video_file.path
        
        def file_iterator(file_path, chunk_size=8192):
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        
        response = StreamingHttpResponse(file_iterator(file_path), content_type='video/mp4')
        # response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"' # Optional
        return response
    except FileNotFoundError:
        raise Http404("Processed video file not found on disk.")
    except Exception as e:
        # Log error e
        raise Http404(f"Error streaming video: {e}")

# The old main_view is now main_dashboard_view
# def main_view(request):
#     return render(request, 'traffic_monitor/placeholder.html')


# API Views
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CombinedChartDataSerializer
# Note: Models VideoUpload, AggregatedData, and Sum are already imported at the top of the file.
# from django.utils import timezone # Not strictly needed for current implementation
# from datetime import timedelta # Not strictly needed for current implementation


def video_detail_view(request, video_id):
    video = get_object_or_404(VideoUpload, id=video_id, status='completed')
    unique_cars = video.unique_car_count # Assumes unique_car_count field exists and is populated

    # Prepare data for the vehicle count over time graph
    graph_data_query = DetectionResult.objects.filter(video=video) \
                                           .values('timestamp_in_video') \
                                           .annotate(total_vehicles=Sum('count')) \
                                           .order_by('timestamp_in_video')

    timestamps = [item['timestamp_in_video'] for item in graph_data_query]
    vehicle_counts = [item['total_vehicles'] for item in graph_data_query]

    context = {
        'video': video,
        'unique_car_count': unique_cars,
        'timestamps': timestamps,
        'vehicle_counts': vehicle_counts,
    }
    return render(request, 'traffic_monitor/video_detail.html', context)


class ChartDataAPIView(APIView):
    def get(self, request, *args, **kwargs):
        distribution_labels = []
        distribution_data = []
        # timeline_labels = [] # Will be new_api_timeline_labels
        # timeline_data = [] # Will be new_api_timeline_data

        latest_video = VideoUpload.objects.filter(status='completed').order_by('-processed_at').first()
        if latest_video:
            # Distribution chart logic (should be fine as AggregatedData now stores unique counts)
            distribution_qs = AggregatedData.objects.filter(video=latest_video).values('vehicle_class').annotate(total_count=Sum('count')).order_by('vehicle_class')
            for item in distribution_qs:
                distribution_labels.append(item['vehicle_class'])
                distribution_data.append(item['total_count'])
        
        # New timeline chart logic for API, similar to main_dashboard_view
        new_api_timeline_labels = []
        new_api_timeline_data = []
        if latest_video:
            detections_over_time_api = DetectionResult.objects.filter(video=latest_video).order_by('timestamp_in_video')

            temp_api_timeline_data = {} # timestamp: count_at_timestamp
            for dr in detections_over_time_api:
                ts = dr.timestamp_in_video
                temp_api_timeline_data[ts] = temp_api_timeline_data.get(ts, 0) + dr.count # Sum counts

            sorted_api_timestamps = sorted(temp_api_timeline_data.keys())
            running_api_total = 0
            for ts in sorted_api_timestamps:
                running_api_total += temp_api_timeline_data[ts]
                new_api_timeline_labels.append(f"{ts:.2f}s")
                new_api_timeline_data.append(running_api_total)

        combined_data = {
            'distribution_chart': {'labels': distribution_labels, 'data': distribution_data},
            'timeline_chart': {'labels': new_api_timeline_labels, 'data': new_api_timeline_data}
        }
        serializer = CombinedChartDataSerializer(combined_data)
        return Response(serializer.data)
