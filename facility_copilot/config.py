"""
FacilityCopilot Configuration
==============================
AWS Bedrock & IoT Core Smart Facility Voice Copilot
"""
import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
BEDROCK_BACKUP_MODEL = os.getenv("BEDROCK_BACKUP_MODEL", "amazon.nova-pro-v1:0")

# Audio and VAD Configuration
SAMPLE_RATE = 16000
SILENCE_THRESHOLD_MS = 450
BARGE_IN_ENABLED = True

# Data Center Facility Thresholds (TIA-942 / ASHRAE TC 9.9)
FACILITY_THRESHOLDS = {
    "rack_temp_max_c": 27.0,      # ASHRAE Recommended A1 Envelope Upper Limit
    "rack_temp_critical_c": 32.0, # Immediate Server Thermal Throttling
    "pue_target": 1.25,           # Target Power Usage Effectiveness
    "ups_min_battery_min": 15.0   # Minimum Runtime on Battery
}
