# Django Traffic Monitoring System

## Description
This application provides a platform for monitoring vehicle traffic from uploaded videos. It uses the YOLOv8 object detection model to identify and count vehicles, stores detection data, and visualizes statistics on a web dashboard. Users can upload videos, view processed videos with detected objects highlighted, and see charts summarizing traffic data.

## Features
*   **Video Upload:** Users can upload video files for processing.
*   **AI-Based Vehicle Detection:** Utilizes a YOLOv8 model (`best.pt`) to detect various vehicle classes.
*   **Data Storage:** Saves video metadata, individual detection events, and aggregated traffic statistics.
*   **Data Visualization:** Displays charts for vehicle distribution by class and traffic volume over time.
*   **Video Streaming:** Allows viewing of processed videos with detection overlays.
*   **Snapshot Capture:** Users can take snapshots from the processed video stream.
*   **Background Processing:** Video processing is handled asynchronously using Celery and Redis.
*   **API Endpoint:** Provides a JSON API for fetching chart data.

## Prerequisites
*   Python (3.8+ recommended)
*   Django (version as per `requirements.txt`, e.g., 5.2.x)
*   Celery
*   Redis (running server instance)
*   `ultralytics` (for YOLOv8)
*   `opencv-python` (for video processing)
*   The `best.pt` YOLOv8 model file (user-provided, trained for vehicle detection).

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    ```

2.  **Navigate to the project directory:**
    ```bash
    cd traffic_project 
    ```
    (Or whatever your root project folder is named, containing `manage.py`)

3.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: See "Known Issues/Limitations" regarding potential issues with full dependency installation in some environments.*

5.  **Place the `best.pt` model file:**
    *   Download or provide your trained `best.pt` YOLOv8 model file.
    *   Place it in the project root directory (the same directory as `manage.py`).

6.  **Ensure Redis server is running:**
    *   Start your Redis server if it's not already running. Default connection is `redis://localhost:6379/0`.

7.  **Apply database migrations:**
    ```bash
    python manage.py makemigrations traffic_monitor 
    python manage.py migrate
    ```

## Running the Application

1.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```

2.  **Start the Celery worker (in a separate terminal):**
    *   Navigate to the project root directory (where `manage.py` is).
    *   Ensure your virtual environment is activated.
    ```bash
    celery -A traffic_project worker -l info
    ```

3.  **Access the application:**
    *   Open your web browser and go to `http://127.0.0.1:8000/`.

## Project Structure (Brief)

*   `traffic_project/`: Contains the main Django project configuration files (`settings.py`, `urls.py`, `celery.py`, `wsgi.py`).
*   `traffic_monitor/`: The core Django application for traffic monitoring.
    *   `models.py`: Defines database models (`VideoUpload`, `DetectionResult`, `AggregatedData`).
    *   `views.py`: Contains view logic for web pages and API endpoints.
    *   `forms.py`: Defines forms (e.g., `VideoUploadForm`).
    *   `tasks.py`: Celery tasks for background processing (e.g., video analysis).
    *   `yolo_processor.py`: Handles the YOLOv8 model loading and video processing logic.
    *   `serializers.py`: Django Rest Framework serializers for API data.
    *   `templates/`: HTML templates for the application.
    *   `static/`: App-specific static files (CSS, JS - if any beyond CDN).
    *   `urls.py`: URL routing for the `traffic_monitor` app.
    *   `tests.py`: Unit tests for the application.
*   `media/`: Directory where uploaded raw videos (`videos/`) and processed videos (`processed_videos/`) are stored (created automatically on upload).
*   `manage.py`: Django's command-line utility for running management commands.
*   `requirements.txt`: A list of Python package dependencies for the project.
*   `README.md`: This file.
*   `best.pt`: (User-provided) The YOLOv8 model file used for vehicle detection. Must be placed in the project root.

## API Endpoints
*   `GET /api/chart-data/`: Retrieves data for the dashboard charts (distribution by class and traffic over time). Response is in JSON format.

## Known Issues/Limitations
*   The development of this project was partly conducted in an environment with significant disk space limitations. This prevented the full installation and testing of all dependencies (e.g., `ultralytics` which has large PyTorch dependencies, `djangorestframework`, `celery[redis]`) and the execution of comprehensive tests using `python manage.py test`. Manual verification of these steps and thorough testing are advised in a full development or production environment.
*   The YOLOv8 model (`best.pt`) is user-provided and its accuracy depends on its training data and configuration.
*   Error handling for video processing can be further enhanced.
*   Frontend charts and video player interactions are implemented with basic client-side JavaScript and Chart.js via CDN.

---
This README provides a guide to understanding, setting up, and running the Django Traffic Monitoring System.
