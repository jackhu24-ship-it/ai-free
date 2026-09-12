// =============================================================================
// C-ABI Foreign Function Interface (FFI) for Python / C / MuJoCo Integration
// Zero-Copy, Thread-Safe, Deterministic Memory Handling
// =============================================================================

use crate::arbiter::CbfSafetyGuard;
use crate::ring_buffer::SpscSharedSlot;
use crate::types::{CandidateAction, JointState, PhysicalSafetyBounds, VerifiedActuatorCommand};

/// Creates a new CBF Safety Guard with default safety bounds and 35ms timeout
#[no_mangle]
pub extern "C" fn safety_guard_create() -> *mut CbfSafetyGuard {
    let guard = Box::new(CbfSafetyGuard::default());
    Box::into_raw(guard)
}

/// Creates a new CBF Safety Guard with custom safety bounds
#[no_mangle]
pub unsafe extern "C" fn safety_guard_create_with_bounds(
    bounds: *const PhysicalSafetyBounds,
    heartbeat_timeout_us: u64,
) -> *mut CbfSafetyGuard {
    if bounds.is_null() {
        return std::ptr::null_mut();
    }
    let guard = Box::new(CbfSafetyGuard::new(*bounds, heartbeat_timeout_us));
    Box::into_raw(guard)
}

/// Deallocates the CBF Safety Guard instance
#[no_mangle]
pub unsafe extern "C" fn safety_guard_destroy(guard: *mut CbfSafetyGuard) {
    if !guard.is_null() {
        drop(Box::from_raw(guard));
    }
}

/// Executes a single fast-loop arbitration cycle (1000 Hz)
#[no_mangle]
pub unsafe extern "C" fn safety_guard_step(
    guard: *mut CbfSafetyGuard,
    state: *const JointState,
    candidate: *const CandidateAction,
    current_time_us: u64,
    out: *mut VerifiedActuatorCommand,
) -> bool {
    if guard.is_null() || state.is_null() || out.is_null() {
        return false;
    }

    let guard_ref = &mut *guard;
    let state_ref = &*state;
    let candidate_opt = if candidate.is_null() {
        None
    } else {
        Some(&*candidate)
    };

    let result = guard_ref.step(state_ref, candidate_opt, current_time_us);
    *out = result;
    true
}

/// Retrieves cumulative cycle statistics from the guard
#[no_mangle]
pub unsafe extern "C" fn safety_guard_get_stats(
    guard: *const CbfSafetyGuard,
    total_cycles: *mut u64,
    total_interventions: *mut u64,
) -> bool {
    if guard.is_null() {
        return false;
    }
    let guard_ref = &*guard;
    if !total_cycles.is_null() {
        *total_cycles = guard_ref.total_cycles;
    }
    if !total_interventions.is_null() {
        *total_interventions = guard_ref.total_interventions;
    }
    true
}

/// Allocates an aligned SPSC Seqlock shared slot
#[no_mangle]
pub extern "C" fn slot_create() -> *mut SpscSharedSlot {
    let slot = Box::new(SpscSharedSlot::new());
    Box::into_raw(slot)
}

/// Deallocates the SPSC Seqlock shared slot
#[no_mangle]
pub unsafe extern "C" fn slot_destroy(slot: *mut SpscSharedSlot) {
    if !slot.is_null() {
        drop(Box::from_raw(slot));
    }
}

/// Producer API: Atomic write candidate action to slot
#[no_mangle]
pub unsafe extern "C" fn slot_write(
    slot: *mut SpscSharedSlot,
    action: *const CandidateAction,
) -> bool {
    if slot.is_null() || action.is_null() {
        return false;
    }
    let slot_ref = &*slot;
    slot_ref.write(&*action);
    true
}

/// Consumer API: Lock-free atomic read from slot with bounded retries
#[no_mangle]
pub unsafe extern "C" fn slot_read(
    slot: *const SpscSharedSlot,
    out: *mut CandidateAction,
) -> bool {
    if slot.is_null() || out.is_null() {
        return false;
    }
    let slot_ref = &*slot;
    slot_ref.read(&mut *out)
}

/// Checks if slot has been initialized by writer
#[no_mangle]
pub unsafe extern "C" fn slot_is_initialized(slot: *const SpscSharedSlot) -> bool {
    if slot.is_null() {
        return false;
    }
    (*slot).is_initialized()
}
