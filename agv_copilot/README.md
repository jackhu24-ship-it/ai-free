# AGVCopilot: Multimodal Voice & Vision AI for Autonomous Mobile Robot Fleets
> **Powered by Google Cloud Vertex AI (Gemini 1.5 Pro) & LangGraph StateGraph**  
> *Targeting Google Cloud Vertex AI & Smart Robotics Hackathons*

[![Google Cloud Vertex AI](https://img.shields.io/badge/Google%20Cloud-Vertex%20AI%20Gemini-4285F4.svg)](https://cloud.google.com/vertex-ai)
[![LangGraph StateGraph](https://img.shields.io/badge/Multi--Agent-LangGraph%20StateGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![ISO 3691-4](https://img.shields.io/badge/Safety%20Standard-ISO%203691--4-green.svg)](https://www.iso.org/)
[![Streamlit UI](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)

---

## 📌 Tagline
> **Multimodal hands-free diagnostic copilot for warehouse AGVs and factory AMRs, correlating live LiDAR point clouds, drive wheel kinematics, and ISO 3691-4 emergency stop protocols in sub-5ms.**

---

## 🏛️ Architecture: Vertex AI Gemini Multimodal + LangGraph StateGraph

```mermaid
flowchart TD
    subgraph Ingestion ["🎥 Multimodal Ingestion Layer"]
        Mic["Technician Mic (WebRTC PCM)"] --> Supervisor["👑 Multimodal Supervisor\n(Gemini 1.5 Pro / Flash)"]
        Cam["Robot Inspection Camera + LiDAR"] --> Supervisor
    end

    subgraph Core_StateGraph ["🧠 LangGraph Parallel Execution"]
        Supervisor -->|Conditional Edge| Kinematics["🏎️ AGV Kinematics Agent\n(CAN / ROS2 Odometry)"]
        Supervisor -->|Conditional Edge| VisionLiDAR["📡 LiDAR & Vision Agent\n(Vertex AI Safety Field Analysis)"]
        Supervisor -->|Conditional Edge| SafetyISO["🛡️ ISO 3691-4 Safety Agent\n(Robotic Emergency Braking RAG)"]

        Kinematics -->|operator.ior State Reducer| Synthesizer["🔊 Synthesizer Node"]
        VisionLiDAR -->|operator.ior State Reducer| Synthesizer
        SafetyISO -->|operator.ior State Reducer| Synthesizer
    end

    subgraph Feedback ["🔊 Feedback Layer"]
        Synthesizer -->|Voice Guidance Stream| Headset["Technician Headset"]
        Synthesizer -->|Fleet Observability| Dashboard["Streamlit Fleet Radar"]
    end
```

## 🚀 Quick Start
```bash
pip install -r requirements.txt
python test_agv_agent.py
streamlit run app.py
```
