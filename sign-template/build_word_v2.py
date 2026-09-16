import sys

sys.stdout.reconfigure(encoding="utf-8")
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

doc = Document()

# Page setup - A4 portrait (210x297mm)
section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.left_margin = Cm(1.5)
section.right_margin = Cm(1.5)
section.top_margin = Cm(1.0)
section.bottom_margin = Cm(1.0)

# Default font
style = doc.styles["Normal"]
font = style.font
font.name = "新細明體"
font.size = Pt(11)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "新細明體")

# Create main table with 6 columns and 40 rows
table = doc.add_table(rows=40, cols=6)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False

# Set column widths (cm)
col_widths = [1.5, 3.0, 3.0, 3.0, 3.0, 4.5]
for row in table.rows:
    for i, cell in enumerate(row.cells):
        cell.width = Cm(col_widths[i])


# Helper to set cell text with formatting
def set_cell(cell, text, bold=False, size=11, align="left", font_name="新細明體"):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
    }[align]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = font_name
    run.element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(size * 1.3)


# Helper to merge cells
def merge_cells(table, r1, c1, r2, c2):
    cell = table.cell(r1, c1)
    cell.merge(table.cell(r2, c2))


# ===== Title =====
merge_cells(table, 0, 0, 0, 5)
set_cell(
    table.cell(0, 0),
    "TGB 台灣金蜂股份有限公司",
    bold=True,
    size=16,
    align="center",
)

# ===== Header Row =====
# 簽呈
merge_cells(table, 1, 0, 2, 2)
set_cell(table.cell(1, 0), "簽    呈", bold=True, size=20, align="center")

# 日期
merge_cells(table, 1, 3, 2, 3)
set_cell(table.cell(1, 3), "2026年07月06日", size=11, align="center")

# 單位
merge_cells(table, 1, 4, 2, 4)
set_cell(table.cell(1, 4), "單 位", bold=True, size=11, align="center")

# 採購課
merge_cells(table, 1, 5, 2, 5)
set_cell(table.cell(1, 5), "採購課", bold=True, size=11, align="center")

# ===== Main Content =====
merge_cells(table, 3, 0, 3, 5)
set_cell(
    table.cell(3, 0),
    "主旨: 深圳市科莱德电子有限公司 UTV 10.4吋中控主機 912791Y 等6項部件單價議決 呈核",
    size=11,
    align="left",
)

merge_cells(table, 4, 0, 4, 5)
set_cell(table.cell(4, 0), "說明:", size=11, align="left")

# Content items
content_items = [
    (5, "一、現狀911918Y 10.4吋中控主機   供應商: 威騰 進貨價:  CNY1890.0 (NT8505.0)"),
    (
        6,
        "       新供應商: 科莱德912791Y 進貨單價議決 CNY908 (NT4086)， 價差NT4419元.降幅51.96%",
    ),
    (7, "二、現狀911913Y/ 960Y(前/後)攝像頭  供應商: 威騰 進貨價:CNY100.0 (NT450.0)"),
    (
        8,
        "       新供應商: 科莱德912793Y/794Y 進貨單價議決 CNY78 (NT351)， 價差NT99元.降幅22%",
    ),
    (9, "三、現狀911914Y 天線盒   供應商: 威騰 進貨價:  CNY28 (NT126.0)"),
    (
        10,
        "       新供應商: 科莱德912789Y(含信號放大器)單價議決 CNY22.0 (NT99)， 價差NT27元.降幅21.42%",
    ),
    (11, "四、現狀911915Y 中控轉接線   供應商: 威騰 進貨價:  CNY190 (NT855)"),
    (
        12,
        "       新供應商: 科莱德912790Y 進貨單價議決 CNY128 (NT576)， 價差NT279元.降幅32.63%",
    ),
    (13, "五、911935Y 藍芽喇叭  供應商: 威騰 進貨價:  CNY361.8 (NT1628.1)"),
    (
        14,
        "        新供應商: 科莱德912792Y 進貨單價議決 CNY300 (NT1350)， 價差NT278.1元.降幅17.08%",
    ),
    (
        15,
        "六、模具與開發費用：CNY188,100  (NT846,450)【開發費用CNY96,000、模具費CNY92,100】",
    ),
    (
        16,
        "       1.模具費：塑膠面殼、塑膠底蓋、矽膠按鍵、防水密封圈模具CNY92,100(NT415,450)",
    ),
    (
        17,
        "                    交貨達15,000台，返還模具費CNY92,100，另藍芽喇叭開發與模具費CNY10,000科萊德承擔",
    ),
    (18, "       2.開發費：開發費用CNY146,000，科萊德承擔CNY50,000，TGB承擔CNY96,000"),
    (19, "        分二期給付：1.合約簽訂時 T/T給付50% CNY94,050 (NT423,225)"),
    (
        20,
        "                                 2.初樣合格 T/T給付50% CNY94,050 (NT423,225)",
    ),
    (21, "七、初樣送樣數量: 付款啟動合約4個月內交付各3PCS(不付費)"),
    (
        22,
        "八、認證：CE→33,000、R10→36,000與FCC→24,000，認證費用小計 93,000 於啟動與獲證各50%T/T給付",
    ),
    (23, "九、付款方式：FOB 深圳港"),
    (24, "        1.前5批量產預付貨款30% T/T給付.尾款70% T/T給付款到發貨。"),
    (25, "        2.第6批起依據船公司裝貨日期(提單日期)起計算 L/C 60天"),
    (26, "十、最低訂購量: 300pcs"),
    (27, "十一、前置期: 45天"),
    (28, "十二、合約書一式二份 併呈請鈞長用印."),
    (29, "             -----------------   以           上  -----------------------"),
    (30, "         呈   核   示"),
]

for row_idx, text in content_items:
    merge_cells(table, row_idx, 0, row_idx, 5)
    is_center = row_idx in [29]
    is_bold = row_idx == 30
    set_cell(
        table.cell(row_idx, 0),
        text,
        bold=is_bold,
        size=11,
        align="center" if is_center else "left",
    )

# Signature table (rows 31-39)
merge_cells(table, 31, 0, 31, 0)
set_cell(table.cell(31, 0), "批\n示", bold=True, size=11, align="center")

merge_cells(table, 31, 1, 31, 1)
set_cell(table.cell(31, 1), "會\n簽\n單\n位", bold=True, size=11, align="center")

merge_cells(table, 31, 2, 31, 2)
set_cell(table.cell(31, 2), "副總經理：\n\n開發部：\n\n營業部：", size=11, align="left")

merge_cells(table, 31, 3, 31, 3)
set_cell(table.cell(31, 3), "單\n位\n主\n管", bold=True, size=11, align="center")

merge_cells(table, 31, 4, 31, 4)
set_cell(table.cell(31, 4), "", size=11, align="center")

merge_cells(table, 31, 5, 31, 5)
set_cell(table.cell(31, 5), "", size=11, align="center")

# Save
output_path = r"C:\260728-code\sign-template\中控議決簽呈模板_v2.docx"
doc.save(output_path)
print("v2 Word 檔已建立:", output_path)
