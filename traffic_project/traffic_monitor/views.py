from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse, Http404
from .forms import VideoUploadForm
from .models import VideoUpload, AggregatedData, DetectionResult, UniqueCarCountTimeSeries # Added UniqueCarCountTimeSeries
from .tasks import process_video_task
from django.db.models import Sum, F, FloatField
# from django.db.models.functions import Cast # Not used in the current implementation of graph_data_query

def main_dashboard_view(request):
    latest_processed_video = VideoUpload.objects.filter(status='completed').order_by('-processed_at').first()
    overall_stats = {'total_vehicles': 0} # Default if no video
    vehicle_breakdown = None
    timeline_labels = []
    timeline_data = []

    if latest_processed_video:
        overall_stats = {'total_vehicles': latest_processed_video.unique_car_count}
        vehicle_breakdown = AggregatedData.objects.filter(video=latest_processed_video).order_by('vehicle_class')

        # Data for "Traffic Over Time" chart from UniqueCarCountTimeSeries
        time_series_data = UniqueCarCountTimeSeries.objects.filter(video=latest_processed_video).order_by('timestamp_in_video')
        if time_series_data.exists():
            timeline_labels = [f"{item.timestamp_in_video:.2f}s" for item in time_series_data] # Formatting for better readability
            timeline_data = [item.cumulative_unique_car_count for item in time_series_data]
        # If no time_series_data, labels and data remain empty lists, which is the desired default

    context = {
        'latest_video': latest_processed_video,
        'overall_stats': overall_stats,
        'vehicle_breakdown': vehicle_breakdown,
        'distribution_labels': [],
        'distribution_data': [],
        'timeline_labels': timeline_labels, # Use the new timeline_labels
        'timeline_data': timeline_data,     # Use the new timeline_data
    }

    if latest_processed_video and vehicle_breakdown:
        context['distribution_labels'] = [item.vehicle_class for item in vehicle_breakdown]
        context['distribution_data'] = [item.count for item in vehicle_breakdown]
    
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
        timeline_labels = []
        timeline_data = []

        latest_video = VideoUpload.objects.filter(status='completed').order_by('-processed_at').first()
        if latest_video:
            distribution_qs = AggregatedData.objects.filter(video=latest_video).values('vehicle_class').annotate(total_count=Sum('count')).order_by('vehicle_class')
            for item in distribution_qs:
                distribution_labels.append(item['vehicle_class'])
                distribution_data.append(item['total_count'])
        
        # For the last 10 processed videos, ordered by upload time (oldest of the 10 first)
        # This API view's timeline data needs to be updated if it's still in use
        # For now, focusing on the main_dashboard_view as per subtask
        recent_videos_qs = VideoUpload.objects.filter(status='completed').order_by('-uploaded_at')[:10]
        # We want them oldest to newest for the chart
        recent_videos = list(reversed(recent_videos_qs))


        for video in recent_videos:
            total_vehicles_for_video = AggregatedData.objects.filter(video=video).aggregate(total=Sum('count'))['total'] or 0
            timeline_labels.append(video.uploaded_at.strftime('%Y-%m-%d %H:%M'))
            timeline_data.append(total_vehicles_for_video)

        combined_data = {
            'distribution_chart': {'labels': distribution_labels, 'data': distribution_data},
            'timeline_chart': {'labels': timeline_labels, 'data': timeline_data}
        }
        serializer = CombinedChartDataSerializer(combined_data)
        return Response(serializer.data)
