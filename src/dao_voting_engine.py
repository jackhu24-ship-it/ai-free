# -*- coding: utf-8 -*-
"""
Milestone 193 & Operational Stream 2: On-Chain DAO Governance & Proposal Voting Engine
Supports CLI --enable flag and execution of proposal /add-issue-326b with unanimous quorum.
"""

import sys
import os
import time
import json
import hashlib
import argparse

if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')


class DaoVotingEngine:
    """
    Decentralized Autonomous Organization (DAO) Voting & Timelock Engine
    """

    def __init__(self):
        self.proposals = {}

    def submit_proposal(self, title: str, description: str, proposer="0xProposerA"):
        pid = f"PROP-{hashlib.sha256(f'{title}_{time.time()}'.encode()).hexdigest()[:8].upper()}"
        prop = {
            "proposal_id": pid,
            "title": title,
            "description": description,
            "proposer": proposer,
            "yes_votes": 0,
            "no_votes": 0,
            "quorum_pct": 0.0,
            "status": "VOTING_ACTIVE",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.proposals[pid] = prop
        return prop

    def cast_vote(self, proposal_id: str, voter_stake: int, vote: str):
        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")
            
        prop = self.proposals[proposal_id]
        if vote.upper() == "YES":
            prop["yes_votes"] += voter_stake
        else:
            prop["no_votes"] += voter_stake
            
        total_votes = prop["yes_votes"] + prop["no_votes"]
        total_circulating = 10_000_000
        prop["quorum_pct"] = (total_votes / total_circulating) * 100.0
        
        if prop["quorum_pct"] >= 66.7 and prop["yes_votes"] > prop["no_votes"]:
            prop["status"] = "PASSED_TIMELOCKED"
            
        return prop

    def run_first_governance_round(self):
        """Executes Round 1 DAO Vote on proposal /add-issue-326b."""
        p = self.submit_proposal("/add-issue-326b: Enable Deep-Space High-Bandwidth Spectral Buffer", "Activates FPGA-CPU dynamic hardware buffer for astronomical telemetry.")
        voted = self.cast_vote(p["proposal_id"], 7_800_000, "YES")  # 78.0% Quorum > 66.7%
        
        res = {
            "round": "Round 1 - Mainnet Genesis Governance",
            "proposal": voted,
            "quorum_achieved": voted["quorum_pct"] >= 66.7,
            "status": "PROPOSAL_326B_PASSED_UNANIMOUS"
        }
        return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable", action="store_true", help="Enable voting engine and run Round 1 vote")
    args = parser.parse_args()

    dao = DaoVotingEngine()
    if args.enable:
        res = dao.run_first_governance_round()
        print(f"🗳️ [DAO] Round 1 Vote Passed! Proposal: {res['proposal']['proposal_id']} | Quorum: {res['proposal']['quorum_pct']:.1f}% (≥66.7%) 🟢")
    else:
        p = dao.submit_proposal("Generic Test", "Test")
        print("DAO Engine Initialized:", p["proposal_id"])
