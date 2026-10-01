# 🎯 TASK SPECIFICATION: Autonomous Sovereign Core 4 Dimensions (TASK-004)
> Target Architecture: PHANTOM GRID - Stage 5 Autonomous Sovereign Organism  
> Environment: Python 3.12+ (Pure Standard Library)  
> Destination: Work in `01_WORKSPACE/` and deliver to `02_OUTBOX/`  
> Authority: 👑 Commander Jack & Executive Secretary Xiaomi  

---

### 【Objective】
Implement the remaining 4 critical dimensions of the PHANTOM GRID 8-Dimension Closed-Loop Topology:
1. **Safety Core**: ISO 26262 ASIL-D Deterministic State Machine (`fsm_core.py`)
2. **Resilience**: Dynamic 4-Tier Thermal Annealing & Backpressure Governor (`hybrid_governor.py`)
3. **Sovereignty**: Tamper-Proof Cryptographic SQLite Audit Ledger (`audit_ledger_sqlite.py`)
4. **Physical Boundary**: 200ms Fail-Safe Watchdog & AUTOSAR E2E Anti-Replay Validator (`hardware_watchdog.py`)
5. **Verification**: Unified Comprehensive Test Suite (`test_sovereign_core.py`)

---

### 【Component Specifications】

#### 1. Module: `fsm_core.py` (ISO 26262 ASIL-D Deterministic State Machine)
- **Class**: `DeterministicFSM`
- **States**: `INIT`, `STANDBY`, `ARMED_AUTONOMOUS`, `DEGRADED_LOCAL`, `EMERGENCY_SHUTDOWN`
- **Strict Allowed Transitions**:
  - `INIT` -> `STANDBY`
  - `STANDBY` -> `ARMED_AUTONOMOUS` | `EMERGENCY_SHUTDOWN`
  - `ARMED_AUTONOMOUS` -> `DEGRADED_LOCAL` | `EMERGENCY_SHUTDOWN` | `STANDBY`
  - `DEGRADED_LOCAL` -> `STANDBY` | `EMERGENCY_SHUTDOWN`
  - `EMERGENCY_SHUTDOWN` -> `INIT` (Requires explicit commander token)
- **Methods**:
  - `transition_to(target_state: str, auth_token: str = None) -> bool`:
    - Enforces legal transitions. Any illegal jump raises `IllegalStateTransitionError`.
    - If transitioning to `EMERGENCY_SHUTDOWN`, immediately triggers safe state lock.
  - `get_current_state() -> str`
  - `get_history() -> List[Dict[str, Any]]`: Returns state transition ledger.

---

#### 2. Module: `hybrid_governor.py` (Dynamic 4-Tier Thermal Annealing & Backpressure)
- **Class**: `HybridTaskGovernor`
- **Tiers**:
  - `TIER_0_CLOUD` (Full Frontier Cloud Inference)
  - `TIER_1_LOCAL_SLM` (Local Ollama / SLM 7B)
  - `TIER_2_TINY_EDGE` (Edge Mini SLM 0.5B)
  - `TIER_3_PURE_RULE` (Deterministic FSM Rules Only)
- **Parameters**: `sliding_window_size: int = 20`, `temp_threshold_c: float = 75.0`, `latency_p99_limit_ms: float = 500.0`
- **Methods**:
  - `record_metric(latency_ms: float, soc_temp_c: float)`: Updates sliding window.
  - `evaluate_tier() -> str`:
    - If `soc_temp_c >= 85.0` or `latency_p99 > 1500.0`: Demotes directly to `TIER_3_PURE_RULE`.
    - Else if `soc_temp_c >= 75.0` or `latency_p99 > 800.0`: Demotes to `TIER_2_TINY_EDGE`.
    - Else if `latency_p99 > 500.0`: Demotes to `TIER_1_LOCAL_SLM`.
    - Else: Operates at `TIER_0_CLOUD`.
  - `get_p99_latency() -> float`

---

#### 3. Module: `audit_ledger_sqlite.py` (Tamper-Proof SQLite Ledger)
- **Class**: `TamperProofAuditLedger`
- **Database**: Local SQLite (or `:memory:` / file path).
- **Schema**:
  - `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - `tx_id TEXT UNIQUE NOT NULL`
  - `prev_hash TEXT NOT NULL`
  - `action TEXT NOT NULL`
  - `payload_json TEXT NOT NULL`
  - `crc32_checksum INTEGER NOT NULL`
  - `commander_sig TEXT NOT NULL`
  - `secretary_sig TEXT NOT NULL`
  - `timestamp TEXT NOT NULL`
  - `block_hash TEXT NOT NULL`
- **Methods**:
  - `record_event(action: str, payload: dict, commander_sig: str, secretary_sig: str) -> str`:
    - Links with `prev_hash` (Genesis hash for first block).
    - Computes CRC32 and SHA-256 block hash.
    - Validates dual signatures (rejects if either signature is missing/empty).
  - `verify_chain_integrity() -> Tuple[bool, int, str]`:
    - Scans entire ledger, recomputes all block hashes and chained links.
    - Returns `(True, total_blocks, "OK")` or `(False, broken_index, "Tamper detected")`.

---

#### 4. Module: `hardware_watchdog.py` (200ms Fail-Safe Watchdog & AUTOSAR E2E Anti-Replay)
- **Class**: `HardwareWatchdog`
  - `feed(source: str)`: Resets countdown timer.
  - `check_heartbeat(current_time_s: float) -> bool`:
    - If elapsed time since last feed > 0.200s (200ms), triggers `FAIL_SILENT_INTERRUPT` (cuts relay output).
  - `is_tripped() -> bool`
- **Class**: `AutosarE2EValidator`
  - `validate_frame(data_bytes: bytes, alive_counter: int, crc8_checksum: int) -> bool`:
    - Alive counter must strictly follow `(last_counter + 1) % 16`. Jumps or repetitions indicate replay attack or dropped frame.
    - Recomputes CRC-8 (SAE J1850 polynomial `0x1D`).
    - Returns `True` if valid, raises `SecurityBreachError` on counter mismatch or CRC corruption.

---

#### 5. Test Suite: `test_sovereign_core.py`
- Comprehensive Pytest assertions testing:
  - FSM state transition validation and illegal transition blocking.
  - Governor dynamic tier demotion under thermal/latency backpressure.
  - SQLite ledger hash chaining, dual-signature enforcement, and tamper detection.
  - Watchdog 200ms timeout interruption and AUTOSAR E2E alive counter validation.

---

### 【Deliverables & Output Rule】
- Deliver all files into `02_OUTBOX/` ready for review.
- Strict Constraints: Pure Python standard library (no external third-party dependencies), zero hardcoded secrets/keys, zero absolute paths.
