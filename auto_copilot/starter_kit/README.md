# voice-agent-langgraph-starter
> **Modular Scaffolding for Sub-300ms Mission-Critical Voice Agents**  
> Powered by AssemblyAI Universal-3 Pro Streaming STT & LangGraph StateGraph.

---

## 🌟 Highlights
- **16kHz WebRTC ➔ AssemblyAI WebSocket**: Clean audio ingestion with custom domain Word Boost.
- **LangGraph Multi-Agent Parallelism**: Safe dictionary merging with `operator.ior` preventing race conditions.
- **Sub-18ms Barge-In**: Instant audio buffer cancellation upon receiving `PartialTranscript`.
- **Streamlit Observability Dashboard**: Dynamic agent cards with `stream_mode="updates"` progressive rendering.

## 🚀 Getting Started
```bash
pip install -r requirements.txt
streamlit run examples/mock_diagnostics.py
```
