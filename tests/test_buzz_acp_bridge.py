import os
import sys
from unittest.mock import MagicMock
import pytest

# 預先 mock dotenv
if "dotenv" not in sys.modules:
    mock_dotenv = MagicMock()
    mock_dotenv.load_dotenv = MagicMock(return_value=True)
    sys.modules["dotenv"] = mock_dotenv

import runpy
import buzz_acp_bridge
from buzz_acp_bridge import BuzzACPBridge


def test_init_default():
    bridge = BuzzACPBridge()
    assert bridge.community_url == "phantom-grid.communities.buzz.xyz"
    assert "Agent_PM" in bridge.agents
    assert "Agent_Coder" in bridge.agents


def test_init_custom_url():
    custom = "https://example.com/community"
    bridge = BuzzACPBridge(community_url=custom)
    assert bridge.community_url == custom


def test_connect_missing_buzz_key(monkeypatch):
    monkeypatch.setattr(buzz_acp_bridge, "BUZZ_PRIVATE_KEY", None)
    bridge = BuzzACPBridge()
    with pytest.raises(ValueError, match="BUZZ_KEY"):
        bridge.connect()


def test_connect_and_deploy_agents(monkeypatch, capsys):
    monkeypatch.setattr(buzz_acp_bridge, "BUZZ_PRIVATE_KEY", "mock_private_key_123")
    bridge = BuzzACPBridge()
    bridge.connect()
    bridge.deploy_agents()
    captured = capsys.readouterr()
    assert "BuzzACPBridge" in captured.out


def test_main_execution_block(monkeypatch):
    monkeypatch.setenv("BUZZ_PRIVATE_KEY", "mock_private_key_123")
    monkeypatch.setenv("BUZZ_KEY", "mock_private_key_123")
    monkeypatch.setattr(buzz_acp_bridge, "BUZZ_PRIVATE_KEY", "mock_private_key_123")
    runpy.run_module("buzz_acp_bridge", run_name="__main__")
