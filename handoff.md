# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **codex-security 掃描工作區**（卡上游限流）：嘗試 5 個 OpenRouter 免費模型，全部撞到 Google AI Studio 上游限流（`upstream_provider_shared_pool`），非 OpenRouter 帳戶問題。
- **Ollama 操作手冊**：從 Gemini 對話整理出完整手册（7 章節），已存工作區＋雲端硬碟。
- **簽呈 Word/PDF 模板製作**（完成）：A4 直向標準格式已重製完成，同步 G:\我的雲端硬碟\簽呈表單\
- **全域技能 auto-approve-command-guide**（完成）：白名單授權方案 A 建立全域技能並備份至 chezmoi
- **《極光下的父愛》繪本短片**（完成）：1 分鐘音畫同步影片＋風吹草動 GIF

## 🚦 目前狀態
- **codex-security**：上游限流，需等 Google 恢復或加自己的 Google API key 到 OpenRouter Integrations
- **Ollama 手冊**：完成，兩份同步（工作區＋雲端硬碟）
- **OpenRouter 帳戶**：3 組 key 都是 free tier（未充值），免費模型每日 50 次上限；但本次問題是上游 provider 限流，不是平台限额
- **簽呈模板**：完成
- **Git 狀態**：工作區乾淨

## ➡️ 下一步
1. **codex-security**：等 Google 上游限流恢復後再試，或加自己的 Google API key 到 OpenRouter Settings > Integrations
2. **專案初始化**：使用者有意在雲端硬碟開新專案資料夾，待下次指定專案名稱與目標
3. **教學素材應用**：將短片、GIF 與語音合成腳本整合至教學或展示中

## ⚠️ 注意事項
- **codex-security 限流根因**：Google AI Studio 的免費共享池已滿，與 OpenRouter 帳戶額度無關；充值 $10 也不會解決此問題
- **OpenRouter 免費模型速率限制**：未充值帳戶 50 次/日、20 RPM；充值 ≥$10 後 1000 次/日
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`
- **API key 不進 repo**：OpenRouter key 僅放 session 環境變數，收工後即消失
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**，勿放雲端硬碟
- **媒體與產出影片不推 GitHub**：`.gitignore` 已自動排除所有 mp4/gif/jpg

## 🕐 最後更新
- 時間：2026-08-07 09:55
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：✅ 已推（92594e4）
- 本次完成：codex-security 限流排查（確認根因）、Ollama 操作手冊建立、合併遠端變更
