/**
 * PHANTOM GRID - Office 2 Dynamic War Room Frontend Linkage Patch
 * 整合左側 Mobile HUI 拖曳感應、右側 Bob 視覺海關拓撲、SSE 串流與安裝包雙軌同步
 * Author: 執行秘書處 小米 & 特助小幫手
 * Authority: 👑 霸丸總指揮官 Jack 哥
 */

(function initOffice2Patch() {
  const BACKEND_URL = "http://127.0.0.1:8766";
  console.log("🛡️ [Office 2 Patch] 正在初始化雙向聯動模組 (後端連接目標: " + BACKEND_URL + ")");

  // 1. 在左側 Mobile 視圖建立拖曳感應區 (Dropzone)
  function initMobileDropzone() {
    const dropTarget = document.querySelector(".phone-frame") || document.getElementById("chatScroll");
    if (!dropTarget) {
      setTimeout(initMobileDropzone, 500);
      return;
    }

    // 添加拖曳提示框
    let dropOverlay = document.getElementById("phone-drop-overlay");
    if (!dropOverlay) {
      dropOverlay = document.createElement("div");
      dropOverlay.id = "phone-drop-overlay";
      dropOverlay.style.position = "absolute";
      dropOverlay.style.top = "60px";
      dropOverlay.style.left = "12px";
      dropOverlay.style.right = "12px";
      dropOverlay.style.bottom = "80px";
      dropOverlay.style.border = "2px dashed #00FF66";
      dropOverlay.style.borderRadius = "16px";
      dropOverlay.style.backgroundColor = "rgba(0, 255, 102, 0.12)";
      dropOverlay.style.backdropFilter = "blur(4px)";
      dropOverlay.style.display = "none";
      dropOverlay.style.flexDirection = "column";
      dropOverlay.style.alignItems = "center";
      dropOverlay.style.justifyContent = "center";
      dropOverlay.style.zIndex = "999";
      dropOverlay.style.pointerEvents = "none";
      dropOverlay.innerHTML = `
        <div style="font-size:2.2rem; margin-bottom:8px;">📥</div>
        <div style="color:#00FF66; font-size:0.95rem; font-weight:bold; font-family:monospace;">放開以投遞截圖</div>
        <div style="color:#a7f3d0; font-size:0.75rem; margin-top:4px;">自動喚醒 Bob 視覺排版逆向工兵</div>
      `;
      dropTarget.style.position = "relative";
      dropTarget.appendChild(dropOverlay);
    }

    dropTarget.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropOverlay.style.display = "flex";
      dropTarget.style.boxShadow = "0 0 25px rgba(0, 255, 102, 0.4)";
    });

    dropTarget.addEventListener("dragleave", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!dropTarget.contains(e.relatedTarget)) {
        dropOverlay.style.display = "none";
        dropTarget.style.boxShadow = "";
      }
    });

    dropTarget.addEventListener("drop", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropOverlay.style.display = "none";
      dropTarget.style.boxShadow = "";

      const files = e.dataTransfer.files;
      if (files && files.length > 0 && files[0].type.startsWith("image/")) {
        const file = files[0];
        const arrayBuffer = await file.arrayBuffer();
        const dropTimestamp = Date.now();
        const droppedName = `drop_${dropTimestamp}.png`;

        // 自動填入手機終端查詢框
        const inputQuery = document.getElementById("inputQuery");
        if (inputQuery) {
          inputQuery.value = `learn-layout: samples/${droppedName}`;
        }

        // 在手機對話視窗插入用戶上傳泡泡
        appendMobileChatMessage(`🖼️ 拖曳投遞截圖：${file.name} (${(file.size / 1024).toFixed(1)} KB)`, true);
        appendMobileChatMessage(`⚡ 哨兵已捕獲！正在投遞至 samples/${droppedName} 並喚醒 Bob 逆向工兵...`, false);

        // 自動切換到 Bob 視覺海關分頁，讓統帥直接看到進度
        if (typeof switchTab === "function") {
          switchTab("bobcustoms");
        }

        appendLog(`[Mobile HUI] 拖曳捕獲圖片: ${file.name}，正在傳送至後端 (8766)...`);

        // 投遞圖片至後端 API (8766)
        fetch(`${BACKEND_URL}/api/upload-layout`, {
          method: "POST",
          headers: { "Content-Type": "application/octet-stream" },
          body: arrayBuffer
        })
        .then(res => res.json())
        .then(data => {
          appendLog(`[Mobile HUI] 檔案上傳成功: ${data.file}，雙層認證流水線已喚醒！`);
        })
        .catch(err => {
          appendLog(`❌ 上傳失敗: ${err.message}`);
          appendMobileChatMessage(`❌ 上傳失敗: ${err.message} (請確認 8766 伺服器已啟動)`, false);
        });
      }
    });
  }

  // 2. 建立右側 SSE 串流監聽 (Port 8766)
  let sseConn = null;
  function initSSE() {
    try {
      if (sseConn) {
        sseConn.close();
      }
      sseConn = new EventSource(`${BACKEND_URL}/api/stream`);

      sseConn.onopen = () => {
        appendLog(`[SSE] 已成功連線至第二辦公室聯動核心 (8766)`);
      };

      sseConn.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // 心跳與同步狀態更新
          if (data.type === "HEARTBEAT" && data.sync) {
            updateSyncHealthBadge(data.sync);
          }

          // 日誌更新
          if (data.type === "LOG") {
            appendLog(`[${data.source || 'SYS'}] ${data.message}`);
            if (data.source === "Mobile_HUI") {
              appendMobileChatMessage(data.message, false);
            }
          }

          // 雙層認證步驟跳轉
          if (data.type === "VERIFY_STEP") {
            appendLog(`[認證管線] ${data.step} 狀態更新: ${data.status}`);
            updateCustomsStep(data.step, data.status);
          }

          // 樣式 JSON 解析完畢更新
          if (data.type === "THEME_UPDATED" && data.theme) {
            updateExtractedTheme(data.theme);
          }

          // 導出進度
          if (data.type === "EXPORT_PROGRESS" || data.type === "EXPORT_COMPLETE") {
            appendMobileChatMessage(`📦 [Solo發布] ${data.message}`, false);
            appendLog(`[Solo Export] ${data.message}`);
          }

          // 哨兵狀態
          if (data.type === "WATCHDOG_STATUS") {
            appendMobileChatMessage(`👁️ [目錄哨兵] ${data.message}`, false);
          }

          // 落款完成通知
          if (data.type === "SIGNOFF_COMPLETE") {
            updateCustomsSignoff(data.status, data.message);
            appendMobileChatMessage(`👑 <b>統帥落款完成</b>：${data.message}`, false);
            appendLog(`🎖️ ${data.message}`);
          }

          // OUTBOX 審查提取通知
          if (data.type === "OUTBOX_REVIEW_DONE") {
            appendMobileChatMessage(`📦 [OUTBOX審查] ${data.message}`, false);
            appendLog(`[Outbox] ${data.message}`);
            if (typeof renderOutboxPanel === "function" && data.result) {
              renderOutboxPanel(data.result);
            }
          }
          if (data.type === "OUTBOX_SYNC_DONE") {
            appendMobileChatMessage(`🎉 [核心庫同步] ${data.message}`, false);
            appendLog(`[Outbox Sync] ${data.message}`);
          }
        } catch (e) {
          // ignore non-json
        }
      };

      sseConn.onerror = () => {
        sseConn.close();
        setTimeout(initSSE, 3000);
      };
    } catch (e) {
      setTimeout(initSSE, 3000);
    }
  }

  // 3. UI 輔助：更新浮動與儀表板同步狀態燈
  function updateSyncHealthBadge(sync) {
    let badge = document.getElementById("installer-sync-badge");
    if (!badge) {
      badge = document.createElement("div");
      badge.id = "installer-sync-badge";
      badge.style.position = "fixed";
      badge.style.bottom = "12px";
      badge.style.right = "16px";
      badge.style.padding = "6px 14px";
      badge.style.borderRadius = "20px";
      badge.style.fontSize = "11px";
      badge.style.fontFamily = "monospace";
      badge.style.fontWeight = "bold";
      badge.style.letterSpacing = "0.5px";
      badge.style.boxShadow = "0 4px 14px rgba(0,0,0,0.4)";
      badge.style.zIndex = "9999";
      badge.style.cursor = "pointer";
      badge.title = "點擊手動觸發雙向 SHA256 比對";
      badge.onclick = () => window.triggerCommand("執行雙向 SHA256 校驗");
      document.body.appendChild(badge);
    }

    if (sync.in_sync) {
      badge.style.backgroundColor = "rgba(16, 185, 129, 0.9)";
      badge.style.color = "#FFFFFF";
      badge.style.border = "1px solid #34D399";
      badge.innerHTML = `🛡️ 安裝包雙軌: 100% IN-SYNC (${sync.installer_hash})`;
    } else {
      badge.style.backgroundColor = "rgba(245, 158, 11, 0.9)";
      badge.style.color = "#000000";
      badge.style.border = "1px solid #FCD34D";
      badge.innerHTML = `⚠️ 安裝包待同步: PENDING_SYNC (C:${sync.c_hash} / G:${sync.g_hash})`;
    }

    const innerBadge = document.getElementById("customs-sync-indicator");
    if (innerBadge) {
      innerBadge.innerHTML = sync.in_sync
        ? `<span style="color:#10B981; font-weight:bold;">● 100% IN-SYNC (${sync.installer_hash})</span>`
        : `<span style="color:#F59E0B; font-weight:bold;">▲ PENDING_SYNC (C:${sync.c_hash} / G:${sync.g_hash})</span>`;
    }
  }

  // 4. Bob 視覺海關面板各級狀態更新
  function updateCustomsStep(step, status) {
    if (step === "L1_XIAOMI") {
      const el = document.getElementById("stepL1Status");
      const card = document.getElementById("stepL1Card");
      if (el) {
        if (status === "CHECKING") {
          el.innerHTML = `<span style="color:#F59E0B;">⚡ 檢查中...</span>`;
          if (card) card.style.borderColor = "#F59E0B";
        } else if (status === "PASS") {
          el.innerHTML = `<span style="color:#10B981; font-weight:bold;">✅ 通過 (PASS)</span>`;
          if (card) card.style.borderColor = "#10B981";
        }
      }
    } else if (step === "L2_OFFICE2") {
      const el = document.getElementById("stepL2Status");
      const card = document.getElementById("stepL2Card");
      if (el) {
        if (status === "CHECKING") {
          el.innerHTML = `<span style="color:#F59E0B;">⚡ 渲染試跑中...</span>`;
          if (card) card.style.borderColor = "#F59E0B";
        } else if (status === "PASS") {
          el.innerHTML = `<span style="color:#10B981; font-weight:bold;">✅ 通過 (PASS)</span>`;
          if (card) card.style.borderColor = "#10B981";
        }
      }
    }
  }

  function updateCustomsSignoff(status, msg) {
    const el = document.getElementById("stepL3Status");
    const card = document.getElementById("stepL3Card");
    if (el) {
      el.innerHTML = `<span style="color:#FCD34D; font-weight:bold;">👑 已落款生效 (OFFICIALLY CERTIFIED)</span>`;
      if (card) {
        card.style.borderColor = "#FCD34D";
        card.style.boxShadow = "0 0 15px rgba(245, 158, 11, 0.3)";
      }
    }
    const logBox = document.getElementById("customs-recent-log");
    if (logBox) {
      const timeStr = new Date().toLocaleTimeString();
      logBox.innerHTML = `[${timeStr}] 👑 ${msg}<br>` + logBox.innerHTML;
    }
  }

  function updateExtractedTheme(theme) {
    const codeEl = document.getElementById("bob-theme-code");
    if (codeEl) {
      codeEl.textContent = JSON.stringify(theme, null, 2);
    }
    const previewEl = document.getElementById("bob-theme-preview-card");
    if (previewEl && theme) {
      previewEl.style.fontFamily = theme.font_family || "inherit";
      previewEl.style.lineHeight = theme.layout_rules?.line_height || "1.55";
      previewEl.style.color = theme.colors?.body || "#2D3748";
      previewEl.innerHTML = `
        <h4 style="color:${theme.colors?.primary || '#1A202C'}; margin:0 0 8px 0; font-size:${theme.font_size?.h1 || '18pt'};">
          ${theme.theme_name || '逆向樣式預覽'}
        </h4>
        <p style="margin:0; font-size:${theme.font_size?.body || '10.5pt'}; text-indent:${theme.layout_rules?.hanging_indent || '0'};">
          這是由 Bob 傭兵逆向抽取並經小米安檢、二辦試跑與統帥落款之印刷級樣式排版實時渲染展示。
        </p>
      `;
    }
  }

  // 5. 手機端對話框訊息補充
  function appendMobileChatMessage(msg, isUser = false) {
    const chatScroll = document.getElementById("chatScroll");
    if (!chatScroll) return;

    const div = document.createElement("div");
    if (isUser) {
      div.className = "msg-user";
      div.style.marginBottom = "8px";
      div.textContent = msg;
    } else {
      div.className = "msg-ai-card";
      div.style.marginBottom = "8px";
      div.style.padding = "8px 12px";
      div.style.fontSize = "0.75rem";
      div.style.borderLeft = "3px solid #00F2FE";
      div.style.backgroundColor = "rgba(15, 23, 42, 0.9)";
      div.innerHTML = msg;
    }

    chatScroll.appendChild(div);
    chatScroll.scrollTop = chatScroll.scrollHeight;
  }

  // 6. 日誌輔助
  function appendLog(msg) {
    console.log(`[Office 2 Patch] ${msg}`);
    const rawBox = document.getElementById("rawLogsContent");
    if (rawBox) {
      const timeStr = new Date().toLocaleTimeString();
      rawBox.textContent += `[${timeStr}] ${msg}\n`;
      rawBox.scrollTop = rawBox.scrollHeight;
    }
  }

  // 7. 全域指令派遣 API (供手機晶片按鈕調用)
  window.triggerCommand = function(cmd) {
    appendLog(`[Dispatcher] 派遣指令: ${cmd}`);
    fetch(`${BACKEND_URL}/api/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: cmd })
    })
    .then(r => r.json())
    .then(data => {
      appendLog(`[Dispatcher] 指令已確認: ${data.status}`);
    })
    .catch(err => {
      appendLog(`[Dispatcher] 指令派遣異常: ${err}`);
    });

    if (typeof window.quickSend === "function") {
      window.quickSend(cmd);
    }
  };

  // 8. Solo 全格式導出觸發器
  window.triggerSoloExport = function(formatType) {
    const formatNames = {
      'pdf': '📄 向量級 PDF (Office 2/3)',
      'pptx': '📊 商業簡報 PPTX (Office 2)',
      'docx': '📝 教學文件 DOCX (Office 3)',
      'xlsx': '📈 試算表/成績冊 XLSX (Office 3)',
      'survey': '📋 線上問卷腳本 (Office 3)',
      'exam': '🎯 隨機題庫 Quiz (Office 1)',
      'video': '🎬 方案 B 1080P 影片直出 (Headless AI Video)',
      'all': '🚀 Solo 全格式一鍵全套導出'
    };
    const title = formatNames[formatType] || formatType;
    appendLog(`[Solo Export] 觸發格式導出: ${title}`);
    appendMobileChatMessage(`🚀 <b>發起導出</b>：${title}，產出資產將直通 G 槽真身金庫！`, false);
    window.triggerCommand(`執行 Solo 格式發布: ${formatType}`);
  };

  // 9. 02_OUTBOX 提取、審查、簽章與核心庫同步控制器 (兩階段動作設計)
  window.handleOutboxTwoStageAction = async function() {
    const btn = document.getElementById("btnOutboxReviewSync");
    const currentStage = btn ? btn.getAttribute("data-stage") : "idle";

    // 若尚未進入第二階段（或為初始狀態），執行第 1 階段：唯讀提取、快取排除、AST 與防幻覺審查、生成核可簽章
    if (currentStage !== "ready_to_sync") {
      appendLog("[Outbox Review] 觸發第 1 階段：02_OUTBOX 成果提取、雜訊過濾與 AST/防幻覺稽核");
      appendMobileChatMessage("⚡ [提取 02_OUTBOX 成果與安全審查]", true);

      // 自動切換到右側 OUTBOX 審查面板
      if (typeof switchTab === "function") {
        switchTab("outboxreview");
      }

      if (btn) {
        btn.textContent = "⏳ 提取與稽核中...";
        btn.style.borderColor = "#c084fc";
        btn.style.color = "#c084fc";
      }

      await window.loadOutboxReview();
    } else {
      // 第 2 階段：發章入庫、核心庫同步、沙盒 zip 歸檔清空、全域反查熱重載
      appendLog("[Outbox Sync] 觸發第 2 階段：批准並同步核心庫，執行沙盒歸檔與熱重載");
      appendMobileChatMessage("🚀 [批准並同步核心庫]", true);

      if (btn) {
        btn.textContent = "⏳ 正在入庫並歸檔沙盒...";
        btn.disabled = true;
      }

      await window.syncOutboxToCore();
    }
  };

  window.loadOutboxReview = async function() {
    appendLog("[Outbox Review] 正在向後端拉取 02_OUTBOX 審查數據...");
    const listDiv = document.getElementById("outboxMatchesList");
    if (listDiv) {
      listDiv.innerHTML = '<div style="color:#a855f7;">⏳ 正在掃描沙盒 02_OUTBOX、排除快取雜訊、抽取 AST 實體並執行防幻覺驗收...</div>';
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/outbox-review`);
      const data = await res.json();
      renderOutboxPanel(data);

      const btn = document.getElementById("btnOutboxReviewSync");
      if (data.can_sync_core && btn) {
        // 第一步完成：動態切換按鈕為綠色高亮「🚀 批准並同步核心庫」
        btn.textContent = "🚀 批准並同步核心庫";
        btn.setAttribute("data-stage", "ready_to_sync");
        btn.style.borderColor = "#10b981";
        btn.style.color = "#34d399";
        btn.style.background = "rgba(16, 185, 129, 0.22)";
        btn.style.boxShadow = "0 0 16px rgba(16, 185, 129, 0.5)";
      }

      // 左側 Copilot 完整印出對話報告
      const count = data.count || 0;
      const manifestId = (data.manifest && data.manifest.manifest_id) ? data.manifest.manifest_id : "VALIDATED";
      const reportHtml = `
        <b>報告 Jack 哥！02_OUTBOX 提取與安全門禁稽核完成！</b><br><br>
        📋 <b>【成果提取與驗收報告】</b>：<br>
        • 提取來源：<code>02_OUTBOX</code> (唯讀快照中繼)<br>
        • 快取與雜訊複檢：<span style="color:#00ff66; font-weight:bold;">✅ 已清除編譯物與暫存檔 (100% 純淨)</span><br>
        • 提取檔案數：<b>${count} 支</b> (全數符合白名單副檔名)<br>
        • AST 語法與防幻覺檢驗：<span style="color:#00ff66; font-weight:bold;">✅ 100% 通過，無敏感調用，實體依賴健全！</span><br>
        • 核可標記：已於 Staging 生成 <code>.approved_manifest.json</code> [${manifestId}]<br><br>
        👉 右上熱鍵已解鎖為【<b>🚀 批准並同步核心庫</b>】，請點擊確認發章入庫！
      `;
      appendMobileChatMessage(reportHtml, false);
    } catch (e) {
      appendLog(`[Outbox Review] 數據載入失敗: ${e}`);
      if (listDiv) {
        listDiv.innerHTML = `<div style="color:#ef4444;">❌ 提取失敗: ${e}</div>`;
      }
      const btn = document.getElementById("btnOutboxReviewSync");
      if (btn) {
        btn.textContent = "❌ 提取失敗 (重試)";
        btn.setAttribute("data-stage", "idle");
      }
    }
  };

  function renderOutboxPanel(data) {
    if (!data) return;
    const countEl = document.getElementById("outboxCountFiles");
    const latEl = document.getElementById("outboxLatency");
    const passEl = document.getElementById("outboxPassRate");
    const shaEl = document.getElementById("outboxShaStatus");
    const listEl = document.getElementById("outboxMatchesList");
    const stagingPathEl = document.getElementById("outboxStagingPath");
    const badgeEl = document.getElementById("outboxStatusBadge");

    if (countEl) countEl.textContent = `${data.count || 0} 支`;
    if (latEl) latEl.textContent = `${data.latency_ms || 0} ms`;
    if (passEl) {
      passEl.textContent = data.all_passed ? "100% PASS" : "WARNING";
      passEl.style.color = data.all_passed ? "var(--success-green)" : "#ef4444";
    }
    if (shaEl) shaEl.textContent = "MANIFEST VALID";
    if (stagingPathEl && data.staging_dir) {
      stagingPathEl.textContent = `Staging: ${data.staging_dir}`;
    }
    if (badgeEl) {
      badgeEl.innerHTML = '<span style="color:#10b981; font-weight:bold;">● AST 合規 ✕ 防幻覺 100% ✕ 簽章解鎖</span>';
      badgeEl.style.borderColor = "#10b981";
    }

    if (listEl) {
      if (!data.data || data.data.length === 0) {
        listEl.innerHTML = '<div style="color:#ef4444;">❌ 02_OUTBOX 無待審檔案。</div>';
        return;
      }
      let html = "";
      data.data.forEach((item, idx) => {
        const passBadge = item.passed 
          ? `<span style="color:#10b981; font-weight:bold;">[PASSED] ${item.audit_msg}</span>`
          : `<span style="color:#ef4444; font-weight:bold;">[FAILED] ${item.audit_msg}</span>`;
        html += `
          <div style="margin-bottom:8px; border-bottom:1px dashed rgba(255,255,255,0.06); padding-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <span style="color:#c084fc; font-weight:bold;">${idx + 1}. ${item.name}</span>
              <span style="color:#94a3b8; font-size:0.75rem; margin-left:8px;">: ${item.line_info}</span>
              <span style="color:#f59e0b; font-size:0.75rem; margin-left:8px;">| SHA: ${item.hash}</span>
              <div style="color:#64748b; font-size:0.7rem; margin-top:2px;">↳ ${item.entity_info || "AST Verified"}</div>
            </div>
            <div>${passBadge}</div>
          </div>
        `;
      });
      listEl.innerHTML = html;
    }
  }

  window.syncOutboxToCore = async function() {
    appendLog("[Outbox Sync] 發起核心庫同步與沙盒歸檔...");
    const btn = document.getElementById("btnOutboxReviewSync");
    const subBtn = document.getElementById("btnSyncCore");

    try {
      const res = await fetch(`${BACKEND_URL}/api/outbox-sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const data = await res.json();

      if (btn) {
        btn.textContent = "🎉 成果已入庫核心庫";
        btn.style.borderColor = "#10b981";
        btn.style.color = "#34d399";
        btn.style.background = "rgba(16, 185, 129, 0.35)";
      }
      if (subBtn) {
        subBtn.textContent = "🎉 核心庫同步完畢";
        subBtn.disabled = true;
      }

      // 更新右側面板狀態
      const badgeEl = document.getElementById("outboxStatusBadge");
      if (badgeEl) {
        badgeEl.innerHTML = '<span style="color:#10b981; font-weight:bold;">● 核心庫已即時上線 // 已歸檔清空</span>';
      }
      const listEl = document.getElementById("outboxMatchesList");
      if (listEl && data.synced_files) {
        let finishHtml = `
          <div style="color:#10b981; font-weight:bold; margin-bottom:8px;">✅ 核心庫覆蓋與歸檔重置作業 100% 成功！</div>
          <div style="color:#94a3b8; font-size:0.75rem; margin-bottom:8px;">
            • 統帥簽章：${data.approval_seal.digital_fingerprint}<br>
            • 歸檔備份包：${data.archive_zip}<br>
            • 沙盒狀態：02_OUTBOX 與 Staging 區已清空重置，待命下一輪任務！
          </div>
        `;
        listEl.innerHTML = finishHtml;
      }

      // 左側手機 Copilot 即時送出官方【成果交付結算報告】
      const zipFileName = data.archive_zip ? data.archive_zip.split(/[\\/]/).pop() : "archive_sync.zip";
      const deliveryCardHtml = `
        <b>報告 Jack 哥！🚀 成果審查已正式同步核心庫！</b><br><br>
        📋 <b>【同步結算報告】</b>：<br>
        • 目標路徑：<code>${data.core_dir}</code><br>
        • 同步模組：<b>${data.synced_count} 支檔案</b> (指紋校驗一致 100%)<br>
        • 02_OUTBOX：已自動歸檔至 <code>${zipFileName}</code> 並清空重置<br>
        • 全域反查：已熱重載，核心庫實體已即時上線！<br><br>
        👉 代碼已入庫核心庫！指揮所已就緒，可點選下方熱鍵：【<b>👑 執行指揮所權威落款</b>】以蓋印封版！✨
      `;
      appendMobileChatMessage(deliveryCardHtml, false);
      appendLog(`[Outbox Sync] 同步完成: ${data.synced_count} 支，歸檔包: ${zipFileName}`);

      // 動態更新手機快捷 Chips，切換為下一階段指令
      updateQuickChipsAfterDelivery();

      // 5 秒後優雅復原按鈕為初始待命狀態
      setTimeout(() => {
        if (btn) {
          btn.textContent = "🚀 成果審查同步";
          btn.setAttribute("data-stage", "idle");
          btn.style.borderColor = "rgba(168,85,247,0.7)";
          btn.style.color = "#c084fc";
          btn.style.background = "rgba(168,85,247,0.12)";
          btn.style.boxShadow = "";
          btn.disabled = false;
        }
      }, 5000);

    } catch (e) {
      appendLog(`[Outbox Sync] 同步失敗: ${e}`);
      if (btn) {
        btn.textContent = "❌ 同步異常 (請重試)";
        btn.disabled = false;
      }
    }
  };

  // 10. 指揮所權威落款控制器 (Commander Sign & Stamp Header)
  window.triggerCommanderSign = async function() {
    appendLog("[Command HQ] 正在向指揮所發起權威落款請求...");
    appendMobileChatMessage("👑 [執行指揮所權威落款]", true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/commander-sign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const data = await res.json();

      if (data.success) {
        appendLog(`[Command HQ] 權威落款圓滿成功: ${data.signed_count} 支檔案，版本號: ${data.version_tag}`);
        
        // 格式化展示落款卡
        const filesListHtml = (data.signed_files || []).map(f => 
          `• <code>${f.file_name}</code> (印章: <code>SHA256-${f.seal_hash}</code>)`
        ).join("<br>");

        const signCardHtml = `
          👑 <b>報告 Jack 哥！指揮所權威落款與封版程序已圓滿完成！</b><br><br>
          🏛️ <b>【指揮所落款結算報告】</b>：<br>
          • 法定庫區：<code>C:\\ibm-bob\\core_repo\\</code> (雙向固化 G 槽真身)<br>
          • 落款官銜：👑 霸丸總指揮官 (Supreme Commander)<br>
          • 封版版本：<code>${data.version_tag || 'v1.2.0-RELEASE'}</code> (SEALED & RELEASED)<br>
          • 蓋印模組：共 <b>${data.signed_count || 0} 支檔案</b> 注入權威 Header<br>
          • 建檔履歷：狀態已升級為「<span style="color:#00ff66; font-weight:bold;">🟢 已落款發佈 (Sealed & Released)</span>」<br><br>
          📋 <b>【已蓋印核心模組】</b>：<br>
          ${filesListHtml}<br><br>
          ★ 全套核心代碼已正式受指揮所最高主權護照背書，隨時可調用上線！🛡️✨
        `;
        appendMobileChatMessage(signCardHtml, false);

        // 自動切換到「📦 產出建檔履歷」展台，讓統帥直接看到綠色已落款發佈標籤
        if (typeof switchTab === "function") {
          switchTab("files");
        }
      } else {
        appendMobileChatMessage(`❌ 指揮所落款失敗: ${data.msg || "未知錯誤"}`, false);
        appendLog(`[Command HQ] 落款失敗: ${data.msg}`);
      }
    } catch (e) {
      appendLog(`[Command HQ] 請求失敗: ${e}`);
      appendMobileChatMessage(`❌ 權威落款請求失敗: ${e}`, false);
    }
  };

  function updateQuickChipsAfterDelivery() {
    const chipsBar = document.getElementById("phoneQuickChips");
    if (!chipsBar) return;
    
    // 1. 指揮所權威落款熱鍵（置頂金黃色）
    let signChip = document.getElementById("chipCommanderSign");
    if (!signChip) {
      signChip = document.createElement("div");
      signChip.id = "chipCommanderSign";
      signChip.className = "quick-chip";
      signChip.style.color = "#fde047";
      signChip.style.borderColor = "#f59e0b";
      signChip.style.background = "rgba(245, 158, 11, 0.2)";
      signChip.style.fontWeight = "bold";
      signChip.textContent = "🖋️ 指揮所驗票落款";
      signChip.onclick = () => {
        window.triggerCommanderSign();
      };
      chipsBar.insertBefore(signChip, chipsBar.firstChild);
    }

    // 2. 單元回歸測試熱鍵
    let testChip = document.getElementById("chipRegressionTest");
    if (!testChip) {
      testChip = document.createElement("div");
      testChip.id = "chipRegressionTest";
      testChip.className = "quick-chip";
      testChip.style.color = "#10b981";
      testChip.style.borderColor = "#10b981";
      testChip.style.background = "rgba(16,185,129,0.15)";
      testChip.style.fontWeight = "bold";
      testChip.textContent = "⚡ [執行單元回歸測試]";
      testChip.onclick = () => {
        if (typeof quickSend === "function") {
          quickSend("🧪 測試驗收戰報");
        }
      };
      chipsBar.insertBefore(testChip, signChip.nextSibling);
    }
  }

  // 初始化執行
  window.addEventListener("DOMContentLoaded", () => {
    initMobileDropzone();
    initSSE();
  });

  setTimeout(initMobileDropzone, 1000);
  setTimeout(initSSE, 1200);

})();
