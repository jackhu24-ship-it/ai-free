// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : phantom_table.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:44:48 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// INTEGRITY    : SHA256:cc1414d544d04599... [VERIFIED]
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : phantom_table.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:42:28 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// INTEGRITY    : SHA256:6dfd36b918eb8ccf... [VERIFIED]
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// =====================================================================
// PHANTOM GRID - Advanced Matrix & Pinout Table Module
// 規範: 支援長篇跨頁自動重複表頭、等寬數據對齊、高可讀斑馬紋
// =====================================================================

#let can-matrix-table(
  signals: ()
) = {
  set text(size: 8.5pt, font: ("Inter", "Noto Sans TC"))
  
  table(
    columns: (1.2fr, 2fr, 0.8fr, 0.8fr, 1fr, 1.2fr, 1fr),
    align: (left, left, center, right, left, right, center),
    stroke: (x, y) => if y == 0 {
      (bottom: 1.2pt + rgb("#0F172A"), top: 0.8pt + rgb("#0F172A"))
    } else {
      (bottom: 0.3pt + rgb("#E2E8F0"))
    },
    // 表頭深灰打底，資料行採 2.5% 微感灰交替，降低長時間閱讀疲勞
    fill: (x, y) => if y == 0 {
      rgb("#F1F5F9")
    } else if calc.even(y) {
      rgb("#F8FAFC")
    } else {
      none
    },
    // 跨頁時自動於次頁頂端重複渲染表頭 (Typst 核心特性)
    table.header(
      [*Message ID*], [*Signal Name*], [*Start Bit*], [*Length*], [*Data Type*], [*Factor / Offset*], [*Safety*]
    ),
    ..signals.flatten()
  )
}

#let pinout-table(
  pins: ()
) = {
  set text(size: 8.5pt)
  table(
    columns: (0.8fr, 1.2fr, 1.5fr, 1.5fr, 2fr),
    align: (center, left, center, center, left),
    stroke: (x, y) => if y == 0 {
      (bottom: 1.2pt + rgb("#0F172A"))
    } else {
      (bottom: 0.3pt + rgb("#E2E8F0"))
    },
    fill: (x, y) => if y == 0 { rgb("#F1F5F9") } else { none },
    table.header(
      [*Pin \#*], [*Terminal Name*], [*I/O Type*], [*Voltage Range*], [*Description / Fallback*]
    ),
    ..pins.flatten()
  )
}
