# AGVCopilot — Official Hackathon Submission Packet
> **Theme**: Google Cloud Vertex AI Hackathon / Robotics & Manufacturing Track  
> **Project Name**: `AGVCopilot — Multimodal Voice & Vision Diagnostic Copilot for AGV Fleets`  
> **Tagline**: `Real-time autonomous robot fleet diagnostic copilot powered by Google Cloud Vertex AI and LangGraph StateGraph.`  
> **Tags**: `Google Cloud Vertex AI`, `Gemini 1.5 Pro`, `LangGraph`, `Robotics`, `AGV`, `LiDAR`, `ISO 3691-4`, `Streamlit`

---

## 1. Project Description
In automated warehouses and manufacturing plants, hundreds of Autonomous Mobile Robots (AMRs) and Automated Guided Vehicles (AGVs) navigate busy aisles. When a unit stops or logs a fault, technicians frequently crawl under the vehicle or work in tight spaces holding tools. Navigating complex robotic service software while inspecting mechanical drivetrains is awkward and dangerous.

**AGVCopilot** delivers a hands-free, multimodal diagnostic assistant. Powered by **Google Cloud Vertex AI (Gemini 1.5 Pro)** and an asynchronous **LangGraph StateGraph**, it correlates spoken queries and live camera frames with 360° LiDAR safety fields and ROS2 wheel kinematics. By checking ISO 3691-4 mobile robot safety limits in under 5 milliseconds, it delivers instant spoken guidance and triggers emergency stop protocols before damage occurs.

## 2. Technical Stack
- **Google Cloud Vertex AI**: Multimodal reasoning via Gemini 1.5 Pro / Flash.
- **LangGraph StateGraph**: Parallel Fan-out/Fan-in orchestration with `operator.ior` state merging.
- **Robotics Integration**: ROS2 / CAN-FD odometry, inverter temperatures, and SICK Safety LiDAR fields.
- **Safety Compliance**: Vector RAG indexed against ISO 3691-4 (Industrial Trucks — Safety Requirements).
- **Streamlit**: Real-time fleet status dashboard with radar-style obstacle distance indicators.
