# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **全域技能 `auto-approve-command-guide` 建置**（完成）：為白名單授權方案 A (`Yes, and always allow`) 建立全域技能並備份至 chezmoi。
- **`opencode-draw-free` GitHub 部件下載與檢測**（完成）：成功下載至 `G:\我的雲端硬碟\學習手冊和安裝部件好地方\opencode-draw-free\`，確認本機版本 100% 一致無須重複安裝。
- **《極光下的父愛》1 分鐘繪本短片與風吹 GIF**（完成）：實作感人劇本、AI 4 幕劇照、風吹草動 GIF、語音旁白與 79 秒音畫同步影片 (`極光下的父愛_1分鐘完整史詩版.mp4`)，並完成資料夾暫存檔清理。
- **codex-security 掃描工作區**（卡額度）：工具已裝，待 8/6 08:00 免費 tier 額度重置後驗證。

## 🚦 目前狀態
- **全域技能庫**：`web-study-manual-builder` 與 `auto-approve-command-guide` 均已發布並測試完畢。
- **短片作品資料夾**：[generated/lion_story/](file:///g:/我的雲端硬碟/260803_opencode/generated/lion_story) 已完成清理，剩餘 7 個核心資產。
- **Git 狀態**：工作區乾淨。

## ➡️ 下一步
1. **教學素材應用**：將產出的短片、風吹 GIF 與語音合成腳本整合至教學或展示中。
2. **codex-security 縮範圍掃描**（8/6 08:00 後）：
   ```powershell
   $env:PYTHONUTF8="1"
   $env:OPENROUTER_API_KEY="sk-or-v1-…"
   cd G:\我的雲端硬碟\260803_opencode
   codex-security scan . --provider openrouter --model "google/gemma-4-31b-it:free" --effort high --auth api-key --headless --path sheets-gas-demo
   ```

## ⚠️ 注意事項
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`
- **API key 不進 repo**：OpenRouter / OpenAI key 僅放 session 環境變數
- **Wordwall 工具位置**：執行主位置 `C:\wordwall-cli-opencode`
- **媒體與產出影片不推 GitHub**：`.gitignore` 已自動排除所有 mp4/gif/jpg

## 🕐 最後更新
- 時間：2026-08-06
- 更新者：小幫手 @ LAPTOP-BSBDEJ2Q
- Git push：✅ 已推 (`3abd7b8`)
- 本次完成：建立 auto-approve 全域技能、下載與比對 opencode-draw-free 部件、製作《極光下的父愛》1分鐘風吹草動動畫短片並清理暫存檔。
