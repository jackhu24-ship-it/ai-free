// =============================================================================
// Embodied AI Neuro-Symbolic Fast-Loop Safety Guard
//
// Philosophy: "Neural network expands upper bound; Symbolic engine defends lower bound."
// Target: WCET < 50 us, Lock-Free SPSC Seqlock, Zero Heap Allocation
// =============================================================================

#![cfg_attr(not(feature = "std"), no_std)]

pub mod arbiter;
pub mod ffi;
pub mod ring_buffer;
pub mod types;

pub use arbiter::CbfSafetyGuard;
pub use ring_buffer::SpscSharedSlot;
pub use types::{
    CandidateAction, GuardStatus, JointState, PhysicalSafetyBounds, VerifiedActuatorCommand,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cbf_projection_clamps_excessive_torque() {
        let bounds = PhysicalSafetyBounds::default();
        let q = 2.75; // Very close to q_max (2.8)
        let qd = 2.0; // Moving fast towards boundary
        let tau_des = 80.0; // Pushing further into limit!

        let (tau_safe, intercepted) =
            CbfSafetyGuard::project_cbf_single_joint(q, qd, tau_des, &bounds, 0);

        assert!(intercepted, "CBF must intercept dangerous torque");
        assert!(
            tau_safe < tau_des,
            "Enforced torque must be substantially reduced or reversed"
        );
        assert!(
            tau_safe <= bounds.tau_max[0] && tau_safe >= -bounds.tau_max[0],
            "Torque must remain within physical envelope"
        );
    }

    #[test]
    fn test_spsc_seqlock_read_write() {
        let slot = SpscSharedSlot::new();
        assert!(!slot.is_initialized());

        let mut candidate = CandidateAction::default();
        candidate.q_des = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6];
        candidate.seq_id = 42;
        candidate.timestamp_us = 1000000;

        slot.write(&candidate);
        assert!(slot.is_initialized());

        let mut read_back = CandidateAction::default();
        let success = slot.read(&mut read_back);
        assert!(success);
        assert_eq!(read_back.seq_id, 42);
        assert_eq!(read_back.q_des, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]);
    }

    #[test]
    fn test_heartbeat_timeout_triggers_emergency_damping() {
        let mut guard = CbfSafetyGuard::default();
        let mut state = JointState::default();
        state.qd = [1.0, -1.0, 0.5, -0.5, 0.2, -0.2];

        let mut candidate = CandidateAction::default();
        candidate.timestamp_us = 100_000; // Old timestamp

        // Current time is 200_000 (100 ms later, timeout is 35 ms)
        let cmd = guard.step(&state, Some(&candidate), 200_000);

        assert_eq!(cmd.status, GuardStatus::EmergencyBraking);
        assert!(cmd.is_intervention);
        assert_eq!(cmd.violation_mask, 0x80);

        // Check damping torque direction opposes velocity
        assert!(cmd.tau_cmd[0] < 0.0);
        assert!(cmd.tau_cmd[1] > 0.0);
    }
}
