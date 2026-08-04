# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
#00-#10＋extras＋技能擴充全部完成；簡報技能已實作第一份成品：
- **開工密碼已啟用**：startup 技能 L0 密碼關卡（環境變數 `STARTUP_PASSWORD`，本機已設）；密碼只存環境變數，不進任何 repo
- **#05 GAS 已部署上線**：#06 Supabase 文字雲（前端 wordcloud-app）＋Netlify 兩站已公開（class-wordcloud / class-demo-jackhu24）
- **Padlet 免費帳戶**：jackhu24@gmail.com（免費 3 板）；學生免帳號即可貼
- **簡報技能集已安裝**：opencode-presentation-skills 5 技能（soil-teaching-deck／pptx-teaching-deck／html-slide-deck／soil-image-deck／yaml-image-deck）在 `~/.config/opencode/skills/`，chezmoi 納管
- **Wordwall CLI 已安裝＋登入**：工具在 **`C:\wordwall-cli-opencode`**（本機執行主位置，已登入，doctor 全過）；skill 在 `~/.config/opencode/skills\wordwall`
- **RDQ 技能已安裝**：需求探索四象限，`~/.config/opencode/skills\rdq`，chezmoi 納管
- **簡報實作一完成**：Agent 工具鏈現況報告 **21 頁**（PPTX＋PDF）已交付 `簡報作品\`，修復 pptxgenjs 負寬度坑（詳見 Obsidian）

## 🚦 目前狀態
- 可運行。工具鏈全部就緒，階段二＋附加全完成，進入階段三（實際運用）。
- **簡報技能**：重開 opencode 後才載入新技能；PPTX 產出需 pptxgenjs（**在產出目錄 npm install pptxgenjs**，全域裝的 require 不到）
- **PPTX 轉 PDF**：本機用 PowerPoint COM 轉（`Presentation.SaveAs(..., 32)`）；COM 開檔失敗通常是 pptx 內有非法 XML（如負 ext）
- **Wordwall**：`~/.wordwall/state.json` 已存登入狀態（跨電腦要各自登入）

## ➡️ 下一步
1. 階段三：實際運用於教學備課（Wordwall 活動、文字雲課堂使用、Padlet 板子）
2. 用 Wordwall 建第一個活動（`python wordwall.py create --content 內容.json --dry-run` → `--editor-check` → 正式建立）
3. （可選）簡報技能試做第二份教材；`draw` skill 未裝（圖片式簡報 Level 3 前置，本機無 AI 生圖）

## ⚠️ 注意事項
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`；改 startup/shutdown 技能後需重開 opencode
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles（`~/.local/share/chezmoi`）是獨立 repo，收工/開工要各自處理
- **chezmoi**：改動 `~/.config/opencode/` 後用 `chezmoi re-add` 同步 source repo，再 commit＋push dotfiles repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**。雲端硬碟對 git repo 同步不穩，勿把工具放雲端硬碟
- **pptxgenjs 負寬度坑（重要）**：`addShape('line', { w: 負值 })` 會寫出 `<a:ext cx="-NNN">` 非法 XML，PowerPoint 整檔拒開（python-pptx 卻讀得到，會誤導判斷）。線寬度恆為正（`Math.abs`＋`Math.min`＋`flipH`）；懷疑損壞時 dump slide XML 搜 `<a:ext cx="-`
- **grab-session 的坑**：Chrome 運作中會刪 DevToolsActivePort 檔，改用 `python wordwall.py grab-session --cdp-url http://127.0.0.1:9333`
- **簡報技能依賴**：Python 3.12.10（winget）＋ PyYAML/Pillow/python-pptx ＋ npm pptxgenjs/playwright
- **setup.ps1 有 bug**：PowerShell 5.1 parser 錯誤，改用手動 pip/playwright 指令
- **簡報作品\ 不推 GitHub**：PPTX/PDF 被 .gitignore＋pre-commit 排除（安全規則）
- GAS 操作技巧、Supabase 金鑰位置、Netlify 點數等見 AGENTS.md 與 Obsidian

## 🕐 最後更新
- 時間：2026-08-05
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：待推
- 本次完成：RDQ 技能安裝（chezmoi 納管，dotfiles 957f727）；簡報技能實作一（Agent 工具鏈現況報告 21 頁，PPTX＋PDF 交付簡報作品\）；修復 pptxgenjs 負寬度坑
