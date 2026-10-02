// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : phantom_theme.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:44:48 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// INTEGRITY    : SHA256:10e918913fec1732... [VERIFIED]
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : phantom_theme.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:42:28 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// INTEGRITY    : SHA256:d6a5a0c6347d060e... [VERIFIED]
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : phantom_theme.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:24:54 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// INTEGRITY    : SHA256:8b787c0666ebd6e2... [VERIFIED]
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : phantom_theme.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:21:00 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// ==========================================
// PHANTOM GRID - Core Document Template (PG-SPEC-2026)
// ==========================================

#let phantom-doc(
  title: "PHANTOM GRID TECHNICAL SPECIFICATION",
  subtitle: "System Engineering & Architecture Layout",
  doc-id: "PG-SPEC-2026-V1",
  version: "1.0.0",
  body
) = {
  // 1. 物理版面與基準網格（8pt Grid）
  set page(
    paper: "a4",
    margin: (top: 24mm, bottom: 24mm, inside: 20mm, outside: 18mm),
    header: context [
      #if counter(page).get().first() > 1 [
        #text(size: 8pt, weight: "medium", fill: rgb("#475569"), font: "Inter")[PHANTOM GRID \/\/ SPEC-2026]
        #h(1fr)
        #text(size: 8pt, fill: rgb("#64748B"), font: "JetBrains Mono")[#doc-id]
        #v(2pt)
        #line(length: 100%, stroke: 0.5pt + rgb("#CBD5E1"))
      ]
    ],
    footer: context [
      #line(length: 100%, stroke: 0.5pt + rgb("#CBD5E1"))
      #v(4pt)
      #text(size: 8pt, fill: rgb("#94A3B8"), font: "Inter")[RESTRICTED \/\/ AUTOMOTIVE & SYSTEM ARCHITECTURE]
      #h(1fr)
      #text(size: 8pt, font: "JetBrains Mono", fill: rgb("#475569"))[Page #counter(page).get().first()]
    ]
  )

  // 2. 文字排版規範（Tabular Figures & Major Third 比例）
  set text(
    font: ("Inter", "Noto Sans TC"),
    size: 10pt,
    fill: rgb("#0F172A"),
    lang: "zh",
    region: "tw",
    features: ("tnum",) // tnum: true (開啟等寬數字對齊 Tabular Figures)
  )

  set par(
    leading: 7pt,          // 17pt 總行高
    justify: true,
    first-line-indent: 0pt
  )
  show par: set block(spacing: 10pt)

  // 3. 階層標題規範 (ISO 1.1.1)
  set heading(numbering: "1.1.1")
  show heading.where(level: 1): it => block(spacing: 18pt)[
    #text(size: 20pt, weight: "bold", fill: rgb("#0A0F1D"))[#it]
    #v(4pt)
    #line(length: 100%, stroke: 1.5pt + rgb("#0066FF"))
  ]
  show heading.where(level: 2): it => block(spacing: 14pt)[
    #text(size: 13pt, weight: "semibold", fill: rgb("#1E293B"))[#it]
  ]

  // 4. 工業級表格標準（去直框、加深表頭）
  set table(
    stroke: (x, y) => if y == 0 { (bottom: 1.2pt + rgb("#0F172A")) } 
                      else { (bottom: 0.4pt + rgb("#E2E8F0")) },
    fill: (x, y) => if y == 0 { rgb("#F8FAFC") } else { none }
  )

  body
}
