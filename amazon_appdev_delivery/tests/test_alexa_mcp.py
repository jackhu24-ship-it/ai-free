# -*- coding: utf-8 -*-
"""
Pytest suite for Alexa+ MCP Autonomous Operations Server.
Verifies all 4 core MCP tools, Bedrock bridge, and self-healing transitions.
"""

import pytest
from amazon_appdev_delivery.core.alexa_mcp_server import AlexaOpsMCPServer
from amazon_appdev_delivery.core.bedrock_client import BedrockClient

def test_bedrock_client_initialization():
    client = BedrockClient()
    assert client.model_id is not None
    res = client.invoke_reasoning("Diagnose incident for checkout-service")
    assert res["status"] == "success"
    assert "output" in res
    assert len(res["output"]) > 0

def test_mcp_server_manifest():
    server = AlexaOpsMCPServer()
    manifest = server.get_tool_manifest()
    assert len(manifest) >= 4
    tool_names = [t["name"] for t in manifest]
    assert "get_fleet_status" in tool_names
    assert "diagnose_service_incident" in tool_names
    assert "trigger_autonomous_healing" in tool_names
    assert "run_chaos_verifier" in tool_names

def test_mcp_fleet_status():
    server = AlexaOpsMCPServer()
    res = server.execute_tool("get_fleet_status", {})
    assert res["status"] == "success"
    assert "fleet_overview" in res
    assert "checkout-service" in res["services"]
    assert res["services"]["checkout-service"]["status"] == "DEGRADED"

def test_mcp_diagnose_and_heal_pipeline():
    server = AlexaOpsMCPServer()
    # Step 1: Diagnose
    diag = server.execute_tool("diagnose_service_incident", {"service_name": "checkout-service"})
    assert diag["status"] == "success"
    assert "incident_id" in diag
    assert "bedrock_analysis" in diag
    
    # Step 2: Autonomous Heal
    heal = server.execute_tool("trigger_autonomous_healing", {
        "service_name": "checkout-service",
        "auto_deploy": True
    })
    assert heal["status"] == "success"
    assert heal["action"] == "SELF_HEALING_DEPLOYED"
    assert heal["new_health_state"]["status"] == "HEALTHY"
    assert heal["new_health_state"]["health_score"] == 100
    assert heal["new_health_state"]["latency_ms"] == 35

    # Step 3: Re-check fleet status
    fleet = server.execute_tool("get_fleet_status", {})
    assert fleet["services"]["checkout-service"]["status"] == "HEALTHY"
    assert fleet["fleet_overview"]["degraded_services"] == 0

def test_mcp_chaos_verifier():
    server = AlexaOpsMCPServer()
    chaos = server.execute_tool("run_chaos_verifier", {"target_service": "checkout-service"})
    assert chaos["status"] == "success"
    assert chaos["recovery_time_ms"] < 200
    assert chaos["mttr_compliance"] == "PASSED (<200ms)"
    assert chaos["resilience_grade"] == "A+"

def test_unknown_tool_handling():
    server = AlexaOpsMCPServer()
    res = server.execute_tool("non_existent_tool", {})
    assert res["status"] == "error"
    assert "Unknown MCP tool" in res["message"]
