import os
import tempfile

from src.nostr_mqtt_ota_engine import (
    BankID,
    BootStatus,
    DualBankOTASandboxEngine,
    FirmwarePackage,
    MQTTTelemetryDispatcher,
    NostrEvent,
    NostrTelemetryGateway,
    OTAState,
    run_self_test,
    sanitize_cell,
)


def test_sanitize_cell():
    assert sanitize_cell("=1+1") == "'=1+1"
    assert sanitize_cell("+SUM(A1)") == "'+SUM(A1)"
    assert sanitize_cell("-10") == "'-10"
    assert sanitize_cell("@ALERT") == "'@ALERT"
    assert sanitize_cell("NORMAL_VALUE") == "NORMAL_VALUE"


def test_firmware_package_serialize_header():
    pkg = FirmwarePackage(
        magic=0xAA55A55A,
        version="v2.1.0",
        target_bank=BankID.BANK_B,
        payload=b"\x90\x90\x90",
        expected_sha256="0" * 64,
        signature="a" * 64,
    )
    header = pkg.serialize_header()
    assert len(header) == 68
    assert header.startswith(b"\xaa\x55\xa5\x5a")


def test_nostr_telemetry_gateway():
    event = NostrTelemetryGateway.create_telemetry_event(
        vin="TWN-PHANTOM-001",
        voltage=13.8,
        currents=[1.2, 2.4],
        dtcs=["U0100"],
    )
    assert isinstance(event, NostrEvent)
    assert event.kind == 30078
    assert "TWN-PHANTOM-001" in event.content

    # Dict representation
    d = event.to_dict()
    assert d["id"] == event.id
    assert d["kind"] == 30078

    # Verification passes
    assert NostrTelemetryGateway.verify_event(event) is True

    # Tampered event ID fails
    tampered_id = NostrEvent(
        id="tampered_id",
        pubkey=event.pubkey,
        created_at=event.created_at,
        kind=event.kind,
        tags=event.tags,
        content=event.content,
        sig=event.sig,
    )
    assert NostrTelemetryGateway.verify_event(tampered_id) is False

    # Tampered signature fails
    tampered_sig = NostrEvent(
        id=event.id,
        pubkey=event.pubkey,
        created_at=event.created_at,
        kind=event.kind,
        tags=event.tags,
        content=event.content,
        sig="0" * 128,
    )
    assert NostrTelemetryGateway.verify_event(tampered_sig) is False


def test_mqtt_telemetry_dispatcher():
    topic, payload = MQTTTelemetryDispatcher.build_telemetry_payload(
        vin="TWN-PHANTOM-002",
        voltage=12.6,
        currents=[0.5, 0.8],
        dtcs=[],
    )
    assert "v1/edge/TWN-PHANTOM-002/telemetry/pdu" in topic
    assert "NORMAL" in payload

    # With DTC
    _, payload_warn = MQTTTelemetryDispatcher.build_telemetry_payload(
        vin="TWN-PHANTOM-002",
        voltage=11.2,
        currents=[15.0],
        dtcs=["P0A80"],
    )
    assert "WARNING" in payload_warn


def test_ota_sandbox_normal_lifecycle():
    engine = DualBankOTASandboxEngine()
    assert engine.active_bank == BankID.BANK_A
    assert engine.boot_status == BootStatus.ACTIVE_COMMITTED
    assert engine.ota_state == OTAState.IDLE

    # Target Bank A branch
    fw_a = engine.create_firmware_package(
        version="v2.0.1", code=b"\x01\x02", target_bank=BankID.BANK_A
    )
    ok_a, _ = engine.trigger_ota_upgrade(fw_a)
    assert ok_a is True
    assert engine.bank_a_version == "v2.0.1"

    # Target Bank B branch
    fw_b = engine.create_firmware_package(
        version="v2.1.0", code=b"\x01\x02\x03\x04", target_bank=BankID.BANK_B
    )
    ok_b, _ = engine.trigger_ota_upgrade(fw_b)
    assert ok_b is True
    assert engine.active_bank == BankID.BANK_B
    assert engine.boot_status == BootStatus.PENDING_TRIAL_BOOT
    assert engine.ota_state == OTAState.TRIAL_BOOTING

    # Commit with heartbeat
    ok_commit, msg = engine.check_watchdog_and_commit(send_heartbeat=True)
    assert ok_commit is True
    assert engine.boot_status == BootStatus.ACTIVE_COMMITTED
    assert engine.ota_state == OTAState.COMMITTED
    assert engine.bank_b_version == "v2.1.0"

    # Calling check_watchdog when not in trial booting
    ok_idle, _ = engine.check_watchdog_and_commit(send_heartbeat=True)
    assert ok_idle is True


def test_ota_sandbox_errors():
    engine = DualBankOTASandboxEngine()

    # Invalid magic
    bad_fw = engine.create_firmware_package("v9.9.9", b"\x00")
    bad_fw.magic = 0x12345678
    ok, err_msg = engine.trigger_ota_upgrade(bad_fw)
    assert ok is False
    assert "Magic Header 錯誤" in err_msg

    # Corrupted payload SHA
    corrupted_fw = engine.create_firmware_package("v9.9.9", b"\x00")
    corrupted_fw.expected_sha256 = "f" * 64
    ok_corrupt, err_sha = engine.trigger_ota_upgrade(corrupted_fw)
    assert ok_corrupt is False
    assert "校驗失敗" in err_sha


def test_ota_sandbox_rollback_and_timeout():
    engine = DualBankOTASandboxEngine()
    fw = engine.create_firmware_package(version="v2.2.0-flaky", code=b"\xde\xad\xbe\xef")
    engine.trigger_ota_upgrade(fw)

    # 1. Trial booting ongoing without heartbeat
    ok_wait, msg_wait = engine.check_watchdog_and_commit(send_heartbeat=False)
    assert ok_wait is True
    assert "進行中" in msg_wait

    # 2. Watchdog timeout rollback
    assert engine.trial_boot_start_time is not None
    engine.trial_boot_start_time -= 35.0
    ok_to, msg_to = engine.check_watchdog_and_commit(send_heartbeat=False)
    assert ok_to is False
    assert "逾時" in msg_to
    assert engine.active_bank == BankID.BANK_A
    assert engine.boot_status == BootStatus.ROLLED_BACK_CORRUPT

    # 3. Panic rollback
    engine.trigger_ota_upgrade(fw)
    ok_panic, msg_panic = engine.check_watchdog_and_commit(send_heartbeat=False, force_panic=True)
    assert ok_panic is False
    assert "Panic" in msg_panic
    assert engine.active_bank == BankID.BANK_A


def test_ota_export_trace_csv():
    engine = DualBankOTASandboxEngine()
    engine._log("TEST_OP", "OK", "Sample detail")
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "ota_trace.csv")
        out = engine.export_trace_csv(csv_path)
        assert os.path.exists(out)
        with open(out, "r", encoding="utf-8") as f:
            content = f.read()
            assert "TEST_OP" in content


def test_run_self_test_entrypoint():
    run_self_test()
