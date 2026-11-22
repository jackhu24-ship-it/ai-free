# PHANToM Grid :: Tournament Brief & Dual-Track Staging Plan
> **Tournament**: Google - Agent Harness on Physical-Engineering's Last Exam (PLE)  
> **Host**: Google Research ✕ Kaggle  
> **Prize Pool**: $400,000 USD (1st: $250,000 / 2nd: $100,000 / 3rd: $50,000)  
> **Deadline**: January 5, 2027 @ 11:59 PM UTC (Taipei: Jan 6, 07:59 AM)  
> **Official URL**: https://www.kaggle.com/competitions/physical-engineerings-last-exam  
> **Official Repo**: https://github.com/google-research/ple  
> **Status**: STAGED & IN EXECUTION (PHASE 1 HARNESS BOOTSTRAP)

---

## 1. Executive Summary & Core Thesis
The **Physical-Engineering's Last Exam (PLE)** benchmark addresses the most critical bottleneck in autonomous physical AI: the ability to solve multi-hour, multi-file, code-compliant engineering problems across **Mechanical, Electrical, Structural, and Civil Engineering**.

**PHANToM Grid Sovereign Agent Harness** integrates:
1. **Mechanical & CAD Routing Core (`PG-MOD-35` / `PG-MOD-38`)**:
   - Zero-clash 3D MEP (Mechanical, Electrical, Plumbing) vector routing and early cutoff boundary closure.
   - 3D CAD geometry deconstruction via topological feature graphs.
2. **Electrical & Cable Sizing Engine (`PG-MOD-36` / `PG-MOD-45`)**:
   - Cable sizing, ampacity derating, voltage drop limits (< 3%), and short-circuit fault tolerance.
3. **World-Action Physical Dynamic Rollout (`PG-MOD-39-WAM`)**:
   - 50-step symplectic mental rollout for spatial collision avoidance and stress compliance.
4. **Agent Behavioral Boundary & Anti-Loop Watchdog (`PG-MOD-24-VIGIL`)**:
   - ASIL-D deterministic sandboxing, loop prevention (< 5 retries), 50GB VRAM hardware E-STOP, and 2-Pass ZDR (0.00MB residual).

---

## 2. Standard 10-Drawer Mapping Plan (Rule 91 Parity)

| Drawer | Directory | Artifacts & Deliverables |
| :---: | :--- | :--- |
| **01** | `01_Specs` | Whitepaper, Four Diagrams (Topology, Sequence, State, Defense Matrix), Table 01. |
| **02** | `02_SourceCode` | Autonomous Agent Harness (`ple_harness/`), CAD/WAM/Vigil kernels, CLI runner. |
| **03** | `03_CoverImage_16x9` | Official 16:9 Banner (1920x1080) with high-contrast HUD aesthetics. |
| **04** | `04_Slides_PDF` | Official 10-Slide Presentation Pitch Deck (Knuth-Plass & HarfBuzz pure vector). |
| **05** | `05_DemoVideo_1440P` | 1440P 60FPS Hollywood Presentation (ACES 2.0, -28dB sound bed, pointer lock). |
| **06** | `06_Test_Reports` | Local PLE Dev Set verification reports, latency assertions (<= 1.85us SRAM). |
| **07** | `07_SubmissionPackage`| Kaggle Notebook submission draft, `submission.yaml`, and writeup copy. |
| **08** | `08_AuditReceipts` | WORM Cryptographic Seal, dual sign-off, and 2-Pass ZDR (0.00MB) receipt. |
| **09** | `09_ChaosReports` | 1,500-Iteration Chaos stress test & 50GB VRAM boundary enforcement. |
| **10** | `10_Releases` | Git release manifest, Apache 2.0 LICENSE, and reproduction package. |

---

## 3. Autonomous Execution Milestones
- **Phase 1**: 10-Drawer Skeleton & Spec-First Whitepaper (Topology, Sequence, State Machine, Defense Matrix).
- **Phase 2**: Clone & Align with `google-research/ple` official evaluation container environment.
- **Phase 3**: Plug PHANToM CAD & WAM kernels into the Harness decision pipeline.
- **Phase 4**: Local Dev Set evaluation (29 tasks) & automated test closure.
- **Phase 5**: Kaggle submission package generation & dual-sign-off WORM sealing.
