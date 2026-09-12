"""
AGVCopilot Configuration
========================
Google Cloud Vertex AI Multimodal Voice & Vision Copilot for AGV/AMR Fleets
"""
import os

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "agv-fleet-copilot-prod")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
VERTEX_MODEL_ID = os.getenv("VERTEX_MODEL_ID", "gemini-1.5-pro-002")
VERTEX_FAST_MODEL = os.getenv("VERTEX_FAST_MODEL", "gemini-1.5-flash-002")

# Audio & Vision Parameters
SAMPLE_RATE = 16000
SILENCE_THRESHOLD_MS = 450
CAMERA_IMAGE_MAX_SIZE = (1024, 768)

# Industrial Autonomous Mobile Robot Safety Thresholds (ISO 3691-4)
AGV_SAFETY_THRESHOLDS = {
    "min_lidar_clearance_m": 0.5,    # Dynamic protective safety zone
    "max_battery_temp_c": 55.0,      # Over-temperature warning
    "max_wheel_slip_ratio": 0.15,    # Traction loss fault
    "emergency_brake_decel_g": 0.6   # ISO 3691-4 emergency deceleration
}
