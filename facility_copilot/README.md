# FacilityCopilot: Hands-Free Voice AI for Data Centers & Semiconductor Cleanrooms
> **Powered by AWS Bedrock, IoT Core & LangGraph StateGraph**  
> *Targeting AWS AI & Industrial Enterprise Hackathons*

[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude%203.5-FF9900.svg)](https://aws.amazon.com/bedrock/)
[![LangGraph StateGraph](https://img.shields.io/badge/Multi--Agent-LangGraph%20StateGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit UI](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)

---

## 📌 Tagline
> **Real-time, hands-free voice diagnostic copilot for mission-critical data center facilities and cleanrooms, orchestrating server rack telemetry, UPS power grids, and ASHRAE compliance in sub-5ms.**

---

## 🏛️ Architecture: AWS Bedrock + LangGraph StateGraph

```mermaid
flowchart TD
    subgraph Voice_FrontEnd ["🎙️ Industrial Hands-Free Ingestion"]
        Mic["Technician Headset (Cleanroom PCM)"] -->|WebSocket| BedrockAgent["AWS Bedrock Supervisor\n(Claude 3.5 Sonnet / Nova Pro)"]
    end

    subgraph StateGraph_Core ["🧠 LangGraph Fan-out / Fan-in StateGraph"]
        BedrockAgent -->|Conditional Edge| RackAgent["📊 Rack Telemetry Agent\n(AWS IoT Core MQTT)"]
        BedrockAgent -->|Conditional Edge| UPSAgent["⚡ UPS Power Grid Agent\n(SNMP / Modbus)"]
        BedrockAgent -->|Conditional Edge| SafetyAgent["🛡️ Compliance Safety Agent\n(ASHRAE TC 9.9 / TIA-942 RAG)"]

        RackAgent -->|operator.ior State Reducer| Synthesizer["🔊 Synthesizer Node"]
        UPSAgent -->|operator.ior State Reducer| Synthesizer
        SafetyAgent -->|operator.ior State Reducer| Synthesizer
    end

    subgraph Output_Layer ["🔊 Output & Control"]
        Synthesizer -->|Voice Response Stream| Speaker["Cleanroom Wireless Headset"]
        Synthesizer -->|Live Telemetry Updates| StreamlitUI["Facility Dashboard"]
    end
```

## 🚀 Quick Start
```bash
pip install -r requirements.txt
python test_facility_agent.py
streamlit run app.py
```
