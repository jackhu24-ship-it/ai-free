"""
AutoCopilot Function Calling Schemas & Data Models
Defines the 3 core tools for AssemblyAI / LLM Function Calling.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# -------------------------------------------------------------
# 1. Tool 1: get_vehicle_telemetry
# -------------------------------------------------------------
SubsystemType = Literal["thermal_management", "powertrain", "battery_pack", "chassis_brakes"]
MetricKeyType = Literal[
    "coolant_temp_c",
    "inverter_temp_c",
    "bus_voltage_v",
    "motor_rpm",
    "coolant_line_pressure_kpa",
    "pack_soc_percent"
]

class GetVehicleTelemetryArgs(BaseModel):
    subsystem: SubsystemType = Field(
        ...,
        description="The specific vehicle subsystem to query."
    )
    metric_keys: List[MetricKeyType] = Field(
        ...,
        description="List of exact metric IDs required to answer the query."
    )

# -------------------------------------------------------------
# 2. Tool 2: read_diagnostic_trouble_codes
# -------------------------------------------------------------
EcuTargetType = Literal["all", "engine_control", "battery_management", "body_control"]

class ReadDiagnosticTroubleCodesArgs(BaseModel):
    ecu_target: EcuTargetType = Field(
        default="all",
        description="Target ECU module to inspect. Default to 'all' if unspecified."
    )
    include_snapshot_data: Optional[bool] = Field(
        default=False,
        description="Whether to fetch freeze-frame telemetry recorded at the moment the fault was triggered."
    )

# -------------------------------------------------------------
# 3. Tool 3: lookup_repair_procedure
# -------------------------------------------------------------
SafetyLevelType = Literal["standard", "high_voltage_hazard", "ASIL_relevant"]

class LookupRepairProcedureArgs(BaseModel):
    query_text: str = Field(
        ...,
        description="Natural language technical search phrase (e.g., 'cooling pump bleeding SOP', 'DTC P0117 threshold resolution')."
    )
    safety_level: Optional[SafetyLevelType] = Field(
        default="standard",
        description="Safety clearance context to ensure relevant PPE or isolation instructions are included."
    )

# -------------------------------------------------------------
# Complete Function Calling Tools Specification (JSON Schema)
# -------------------------------------------------------------
FUNCTION_CALLING_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_telemetry",
            "description": "Reads real-time physical sensor metrics from the target vehicle/system via CAN/OBD gateway. Call this whenever the user asks for live temperature, voltage, RPM, or pressure readings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subsystem": {
                        "type": "string",
                        "enum": ["thermal_management", "powertrain", "battery_pack", "chassis_brakes"],
                        "description": "The specific vehicle subsystem to query."
                    },
                    "metric_keys": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "coolant_temp_c",
                                "inverter_temp_c",
                                "bus_voltage_v",
                                "motor_rpm",
                                "coolant_line_pressure_kpa",
                                "pack_soc_percent"
                            ]
                        },
                        "description": "List of exact metric IDs required to answer the query."
                    }
                },
                "required": ["subsystem", "metric_keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_diagnostic_trouble_codes",
            "description": "Retrieves active and pending Diagnostic Trouble Codes (DTC) according to ISO 14229 / OBD-II standards. Call this when checking for active errors, faults, or system warnings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ecu_target": {
                        "type": "string",
                        "enum": ["all", "engine_control", "battery_management", "body_control"],
                        "description": "Target ECU module to inspect. Default to 'all' if unspecified."
                    },
                    "include_snapshot_data": {
                        "type": "boolean",
                        "description": "Whether to fetch freeze-frame telemetry recorded at the moment the fault was triggered."
                    }
                },
                "required": ["ecu_target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_repair_procedure",
            "description": "Queries the vector knowledge base for official service manuals, ISO safety requirements, and step-by-step troubleshooting SOPs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "Natural language technical search phrase (e.g., 'cooling pump bleeding SOP', 'DTC P0117 threshold resolution')."
                    },
                    "safety_level": {
                        "type": "string",
                        "enum": ["standard", "high_voltage_hazard", "ASIL_relevant"],
                        "description": "Safety clearance context to ensure relevant PPE or isolation instructions are included."
                    }
                },
                "required": ["query_text"]
            }
        }
    }
]
