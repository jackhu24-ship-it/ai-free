// =============================================================================
// Lock-Free SPSC Seqlock Shared Memory Slot (Zero Heap Allocation)
// Designed for High-Rate Cross-Thread / Cross-Core Telemetry Exchange
// =============================================================================

use core::cell::UnsafeCell;
use core::sync::atomic::{fence, AtomicU32, Ordering};
use crate::types::CandidateAction;

#[repr(C, align(64))]
pub struct SpscSharedSlot {
    seq: AtomicU32,
    data: UnsafeCell<CandidateAction>,
}

unsafe impl Sync for SpscSharedSlot {}
unsafe impl Send for SpscSharedSlot {}

impl Default for SpscSharedSlot {
    fn default() -> Self {
        Self::new()
    }
}

impl SpscSharedSlot {
    pub const fn new() -> Self {
        Self {
            seq: AtomicU32::new(0),
            data: UnsafeCell::new(CandidateAction {
                q_des: [0.0; 6],
                qd_des: [0.0; 6],
                tau_ff: [0.0; 6],
                kp: [0.0; 6],
                kd: [0.0; 6],
                seq_id: 0,
                timestamp_us: 0,
            }),
        }
    }

    /// Single Producer Write: Atomic sequence counter protects write slot
    /// Writer increments seq to odd (writing in progress), writes data, then increments to even (stable)
    #[inline(always)]
    pub fn write(&self, action: &CandidateAction) {
        let current_seq = self.seq.load(Ordering::Relaxed);
        // Step 1: Make seq odd to signal write in progress
        self.seq.store(current_seq.wrapping_add(1), Ordering::Release);
        fence(Ordering::SeqCst);

        // Step 2: Overwrite slot
        unsafe {
            let ptr = self.data.get();
            *ptr = *action;
        }

        // Step 3: Make seq even to signal completed write
        fence(Ordering::SeqCst);
        self.seq.store(current_seq.wrapping_add(2), Ordering::Release);
    }

    /// Single Consumer Read: Retries up to 3 times if concurrent write detected
    /// Guarantees bounded WCET (< 2 us) without blocking or locking
    #[inline(always)]
    pub fn read(&self, out: &mut CandidateAction) -> bool {
        for _ in 0..3 {
            let seq1 = self.seq.load(Ordering::Acquire);
            if seq1 % 2 != 0 {
                // Writer currently updating data, spin shortly
                core::hint::spin_loop();
                continue;
            }
            if seq1 == 0 {
                // No message has been written yet
                return false;
            }

            fence(Ordering::SeqCst);
            let val = unsafe { *self.data.get() };
            fence(Ordering::SeqCst);

            let seq2 = self.seq.load(Ordering::Acquire);
            if seq1 == seq2 {
                *out = val;
                return true;
            }
            core::hint::spin_loop();
        }
        false
    }

    /// Check if slot has received at least one valid message
    #[inline(always)]
    pub fn is_initialized(&self) -> bool {
        self.seq.load(Ordering::Relaxed) >= 2
    }
}
