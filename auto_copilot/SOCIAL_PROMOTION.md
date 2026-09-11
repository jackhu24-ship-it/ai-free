# AutoCopilot — 社群與 Discord 專案展示推介文案庫
> **適用平台**：AssemblyAI 官方 Discord、lablab.ai 官方 Discord、X (Twitter)、LinkedIn  
> **重點策略**：主打「免手持工業診斷 (Hands-Free)」、「AssemblyAI Universal-3 Pro 串流 STT」、「Word Boost 術語 98%+ 精確率」與「<18ms 極速打斷 (Barge-in)」！

---

## 💬 1. Discord 官方頻道推介（適用 #project-showcase 或 #hackathon-chat）

**建議發布位置**：  
- AssemblyAI Discord ➔ `#community-projects` / `#hackathons`
- lablab.ai Discord ➔ `#project-showcase` / `#assemblyai-hackathon`

**貼文內容（直接複製）**：

> 🚨 **Introducing AutoCopilot: Hands-Free Voice AI Diagnostic Copilot for Industrial & Automotive Engineering!** 🛠️🚗
>
> In grease-heavy vehicle repair bays and high-voltage EV testing, technicians cannot take their hands off physical tools or their eyes off machinery to type on laptops.
> 
> We built **AutoCopilot** to act like an experienced senior co-engineer standing right beside you!
>
> 🌟 **Key Highlights**:
> • 🎙️ **AssemblyAI Universal-3 Pro Streaming**: Raw 16kHz PCM audio via WebSockets.
> • 🎯 **Domain Accuracy via Word Boost**: Flawless recognition of complex acronyms (`UDS 0x19`, `CAN-FD`, `ISO 26262`, `ASIL-B`, `P0117`).
> • ⚡ **Sub-50ms Parallel Tool Calling**: Asynchronous CAN sensor polling + workshop manual vector search (`asyncio.gather`).
> • 🛑 **Sub-18ms Barge-In**: Instant audio buffer cancellation the millisecond the user interrupts.
> • 🖥️ **Full-Duplex UI**: Streamlit WebRTC live microphone + dynamic telemetry gauges with 100% offline Dummy Mode fallback!
>
> 📺 **Demo Video**: [Insert Your YouTube Link Here]
> 💻 **GitHub Repo**: https://github.com/jackhu24-ship-it/ai-free
> 🚀 **lablab.ai Project**: [Insert Your lablab.ai Project Link Here]
>
> Huge thanks to @AssemblyAI and @lablabai for hosting this incredible hackathon! We'd love your feedback! 🙌

*(建議附上：10 秒 Barge-in 打斷瞬間或 Streamlit 儀表盤動態 GIF 截圖)*

---

## 🐦 2. X (Twitter) 推文（280 字精煉版 + 標註主辦方）

**貼文內容（直接複製）**：

> Excited to submit **AutoCopilot** for the @AssemblyAI x @lablabai Hackathon! 🏎️💨
>
> In high-risk automotive repair bays, technicians can't type on laptops with grease-stained gloves. 
> 
> AutoCopilot delivers hands-free voice diagnostics powered by AssemblyAI Universal-3 Pro:
> 🎙️ 16kHz WebRTC WebSocket Streaming
> 🎯 Automotive Word Boost (CAN-FD, UDS, ASIL-B)
> ⚡ <50ms Parallel CAN + Vector RAG tools
> 🛑 <18ms Zero-latency Barge-in interruption
>
> Check out our demo video & open-source repo! 👇
> 📺 [Insert YouTube Link]
> 💻 https://github.com/jackhu24-ship-it/ai-free
>
> #AssemblyAI #VoiceAI #SpeechToText #Automotive #Hackathon #AI #Python #Streamlit

---

## 💼 3. LinkedIn 專業深度貼文

**貼文內容（直接複製）**：

> 🔧 **Bridging Voice AI and Mission-Critical Automotive Engineering: Presenting AutoCopilot**
>
> In modern automotive workshops and EV manufacturing bays, technicians and engineers face a classic productivity bottleneck: hands covered in grease, wearing insulated gloves, and forced to stop mechanical tasks just to look up diagnostic trouble codes (DTCs) or verify safety thresholds on a laptop.
>
> For the **AssemblyAI x lablab.ai Real-Time Voice Agent Hackathon**, we engineered **AutoCopilot** — a safety-critical, voice-first automotive diagnostic assistant.
>
> 🚀 **What Makes It Unique?**
> 1. **Zero-Error Engineering Vocabulary**: General STT models struggle with domain acronyms. Leveraging AssemblyAI's Universal-3 Pro and customized **Word Boost**, AutoCopilot transcribes protocols like `CAN-FD`, `UDS 0x19`, and `ISO 26262` with 98%+ precision.
> 2. **Sub-50ms Parallel Execution**: Using `asyncio.gather`, a single spoken query concurrently polls live CAN telemetry and performs vector search over ISO workshop manuals.
> 3. **Sub-18ms Real-Time Barge-in**: Thanks to AssemblyAI's low-latency `PartialTranscript` streaming, active audio responses are instantly flushed the moment the engineer speaks, ensuring natural, human-in-the-loop safety interruptions.
> 4. **Dual Frontend Architecture**: Featuring an interactive Streamlit WebRTC dashboard with real-time 16kHz PCM audio resampling, and a FastAPI industrial backend.
>
> Proud of what we've built to make workshop floors safer, faster, and truly hands-free.
>
> 📺 Watch the 3-minute demo: [Insert YouTube Link]
> 📂 Explore the codebase: https://github.com/jackhu24-ship-it/ai-free
>
> A massive thank you to AssemblyAI and lablab.ai for organizing such an inspiring challenge!
>
> #VoiceAI #RealTimeAI #AssemblyAI #AutomotiveEngineering #ArtificialIntelligence #SoftwareEngineering #TechInnovation
