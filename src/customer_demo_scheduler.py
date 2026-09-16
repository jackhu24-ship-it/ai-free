# -*- coding: utf-8 -*-
"""
StarChain Customer-Facing Demo Scheduler
Manages customer live demonstration sessions, scheduled multi-modal trials, and real-time execution HUD.
"""

import sys
import os
import time
import json
import hashlib
import secrets

if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from e2e_field_trial_pipeline import E2EFieldTrialPipeline


class CustomerDemoScheduler:
    """
    Live Demo Session & Telemetry Scheduler for Customer-Facing Presentations
    """

    def __init__(self):
        self.pipeline = E2EFieldTrialPipeline(enable_anomaly_webhook=True)
        self.active_sessions = {}
        self.session_logs = []

    def create_customer_session(self, customer_org="NASA_ESA_Global_Consortium", presenter_id="Agent_PM_小幫手"):
        """Initializes an interactive demo session with PQC and cross-chain capabilities."""
        session_id = f"DEMO-{secrets.token_hex(4).upper()}"
        session_meta = {
            "session_id": session_id,
            "customer_org": customer_org,
            "presenter_id": presenter_id,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "LIVE_ACTIVE",
            "pqc_security_level": "NIST Level 3 & Level 5",
            "trials_run": 0
        }
        self.active_sessions[session_id] = session_meta
        return session_meta

    def execute_live_demo_step(self, session_id: str, target_name="JWST_SMACS0723_CustomerLive"):
        """Runs a live observation cycle under the customer session."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found or expired")
            
        t_start = time.perf_counter()
        trial_result = self.pipeline.run_embodied_observation_cycle(target_name=target_name)
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        
        self.active_sessions[session_id]["trials_run"] += 1
        
        log_entry = {
            "session_id": session_id,
            "trial_seq": self.active_sessions[session_id]["trials_run"],
            "target": target_name,
            "source_tx_hash": trial_result["source_tx_hash"],
            "cross_chain_msg_id": trial_result["cross_chain_msg_id"],
            "e2e_latency_ms": elapsed_ms,
            "pqc_security": trial_result["pqc_security_level"],
            "validator_status": trial_result["validator_attestation"]["status"],
            "timestamp": time.time()
        }
        self.session_logs.append(log_entry)
        return {
            "session_id": session_id,
            "execution_status": "CUSTOMER_DEMO_TRIAL_SUCCESS",
            "trial_details": log_entry
        }

    def close_customer_session(self, session_id: str):
        """Closes the customer demo session and outputs final summary."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["status"] = "COMPLETED_SEALED"
            self.active_sessions[session_id]["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            return self.active_sessions[session_id]
        raise ValueError(f"Session {session_id} not active")


if __name__ == "__main__":
    scheduler = CustomerDemoScheduler()
    sess = scheduler.create_customer_session("Global_Astronomy_Alliance")
    print(f"Session Created: {sess['session_id']} for {sess['customer_org']}")
    demo_res = scheduler.execute_live_demo_step(sess["session_id"], "M87_Supermassive_Black_Hole")
    print("Demo Trial Run:", demo_res["execution_status"], "| Latency:", f"{demo_res['trial_details']['e2e_latency_ms']:.3f} ms")
    closed = scheduler.close_customer_session(sess["session_id"])
    print("Demo Session Closed:", closed["status"])
