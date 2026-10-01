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

  // 初始化執行
  window.addEventListener("DOMContentLoaded", () => {
    initMobileDropzone();
    initSSE();
  });

  setTimeout(initMobileDropzone, 1000);
  setTimeout(initSSE, 1200);

})();
