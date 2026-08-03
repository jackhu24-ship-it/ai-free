// netlify/functions/ask-ai.mjs
// 前端呼叫這支函式；金鑰只存在 Netlify 伺服器上，前端永遠拿不到。

export default async (req) => {
  const json = (obj, status = 200) =>
    new Response(JSON.stringify(obj), {
      status,
      headers: { "Content-Type": "application/json; charset=utf-8" }
    });

  if (req.method !== "POST") {
    return json({ error: "只接受 POST" }, 405);
  }

  // ① 從 Netlify 的環境變數拿金鑰（不是從前端拿）
  const apiKey = process.env.AI_API_KEY;
  if (!apiKey) {
    return json({ error: "伺服器還沒設定 AI_API_KEY" }, 500);
  }

  // ② 讀前端送來的問題
  let question = "";
  try {
    const body = await req.json();
    question = String(body.question ?? "").trim();
  } catch {
    return json({ error: "請求格式不對，要送 JSON" }, 400);
  }
  if (!question) {
    return json({ error: "問題是空的" }, 400);
  }
  if (question.length > 500) {
    return json({ error: "問題太長，請縮短到 500 字以內" }, 400);
  }

  // ③ 帶著金鑰去打外部 AI API
  const upstream = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: "llama-3.3-70b-versatile",
      messages: [
        { role: "system", content: "你是國中小老師的教學助理。請用繁體中文回答，200 字以內。" },
        { role: "user", content: question }
      ]
    })
  });

  if (!upstream.ok) {
    // 錯誤細節只寫進伺服器日誌，不回給前端
    console.error("上游 API 錯誤：", upstream.status, await upstream.text());
    return json({ error: "AI 服務暫時無法使用，請稍後再試" }, 502);
  }

  const data = await upstream.json();
  const answer = data.choices?.[0]?.message?.content ?? "（沒有拿到回覆）";

  return json({ answer });
};

// ④ 自訂網址：前端就用 fetch("/api/ask-ai") 呼叫
export const config = { path: "/api/ask-ai" };
