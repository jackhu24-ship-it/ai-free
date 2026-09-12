# FacilityCopilot — Official Hackathon Submission Packet
> **Theme**: AWS Bedrock Enterprise Challenge / Smart Manufacturing  
> **Project Name**: `FacilityCopilot — Hands-Free Voice AI for Mission-Critical Facilities`  
> **Tagline**: `Real-time data center facility diagnostic voice copilot powered by AWS Bedrock and LangGraph StateGraph.`  
> **Tags**: `AWS Bedrock`, `LangGraph`, `Real-Time Voice`, `Multi-Agent`, `Data Center`, `IoT`, `Python`, `Streamlit`

---

## 1. Project Description
Data center facility managers and semiconductor cleanroom engineers operate in environments requiring specialized bunny suits, insulated gloves, and hands on calibration equipment. Halting physical diagnostics to log in and type on laptops creates operational friction and safety risks.

**FacilityCopilot** acts as a senior co-engineer on the technician headset. Powered by **AWS Bedrock** and a decoupled **LangGraph StateGraph**, it ingests real-time spoken queries, concurrently polls server rack inlet temperatures (AWS IoT Core), checks UPS battery backup runtimes (SNMP), and vector searches ASHRAE TC 9.9 standards, assembling verified operational responses in sub-5 milliseconds.

## 2. Technical Stack
- **Amazon Bedrock**: Intent reasoning with Claude 3.5 Sonnet & Nova Pro.
- **LangGraph StateGraph**: Parallel Fan-out/Fan-in orchestration with `operator.ior` state dictionary merging.
- **AWS IoT Core**: Real-time MQTT streaming of server rack temperatures, chilled water flow, and PUE.
- **Streamlit**: Dual-view interactive dashboard with progressive state indicator cards.
- **Barge-in**: Sub-18ms speech cancellation token for instant human interruption.
