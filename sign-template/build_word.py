import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Cm, Twips, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# Page setup - A4 landscape
section = doc.sections[0]
section.page_width = Cm(29.7)
section.page_height = Cm(21.0)
section.left_margin = Cm(0.8)
section.right_margin = Cm(0.8)
section.top_margin = Cm(0.5)
section.bottom_margin = Cm(0.5)

# Default font
style = doc.styles['Normal']
font = style.font
font.name = '新細明體'
font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '新細明體')

# Create table with 17 columns and 39 rows
table = doc.add_table(rows=39, cols=17)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False

# Set column widths based on Excel (in twips)
col_widths_twips = [704, 1536, 1536, 1536, 1536, 1536, 1536, 1536, 1536, 1536, 1536, 1536, 1536, 2176, 1984, 1536, 1408]
for row in table.rows:
    for i, cell in enumerate(row.cells):
        cell.width = Emu(int(col_widths_twips[i] * 635))

# Set row heights (in twips) - 39 rows
row_heights = [375, 525, 525, 525, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 439, 525, 525, 525, 525, 180, 600, 600]
for i, row in enumerate(table.rows):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    trHeight = OxmlElement('w:trHeight')
    trHeight.set(qn('w:val'), str(int(row_heights[i] * 20)))
    trHeight.set(qn('w:hRule'), 'atLeast')
    trPr.append(trHeight)

# Helper to set cell text with formatting
def set_cell(cell, text, bold=False, size=11, align='left', font_name='新細明體'):
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER, 'right': WD_ALIGN_PARAGRAPH.RIGHT}[align]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = font_name
    run.element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(size * 1.2)

# Helper to merge cells
def merge_cells(table, r1, c1, r2, c2):
    cell = table.cell(r1, c1)
    cell.merge(table.cell(r2, c2))

# ===== Fill content based on Excel data =====

# Row 0-1: Title merged across cols 3-15
merge_cells(table, 0, 3, 1, 15)
set_cell(table.cell(0, 3), 'TGB 台灣金蜂股份有限公司', bold=True, size=18, align='center')

# Row 2-3: '簽呈' at col 1-9
merge_cells(table, 2, 1, 3, 9)
set_cell(table.cell(2, 1), '簽    呈', bold=True, size=20, align='left')

# Row 2-3: '單位' at col 10-11
merge_cells(table, 2, 10, 3, 11)
set_cell(table.cell(2, 10), '單   位', bold=True, size=20, align='center')

# Row 2-3: '採購課' at col 12-14
merge_cells(table, 2, 12, 3, 14)
set_cell(table.cell(2, 12), '採購課', bold=True, size=20, align='center')

# Row 4: Subject merged across cols 1-15
merge_cells(table, 4, 1, 4, 15)
set_cell(table.cell(4, 1), '主旨: 深圳市科莱德电子有限公司 UTV 10.4吋中控主機 912791Y 等6項部件單價議決 呈核', size=11, align='left')

# Row 5: 說明
merge_cells(table, 5, 1, 5, 15)
set_cell(table.cell(5, 1), '說明:', size=11, align='left')

# Rows 6-30: Content items (merged across cols 1-15)
content_rows = [
    (6, '一、現狀911918Y 10.4吋中控主機   供應商: 威騰 進貨價:  CNY1890.0 (NT8505.0)'),
    (7, '       新供應商: 科莱德912791Y 進貨單價議決 CNY908 (NT4086)， 價差NT4419元.降幅51.96%'),
    (8, '二、現狀911913Y/ 960Y(前/後)攝像頭  供應商: 威騰 進貨價:CNY100.0 (NT450.0)'),
    (9, '       新供應商: 科莱德912793Y/794Y 進貨單價議決 CNY78 (NT351)， 價差NT99元.降幅22%'),
    (10, '三、現狀911914Y 天線盒   供應商: 威騰 進貨價:  CNY28 (NT126.0)'),
    (11, '       新供應商: 科莱德912789Y(含信號放大器)單價議決 CNY22.0 (NT99)， 價差NT27元.降幅21.42%'),
    (12, '四、現狀911915Y 中控轉接線   供應商: 威騰 進貨價:  CNY190 (NT855)'),
    (13, '       新供應商: 科莱德912790Y 進貨單價議決 CNY128 (NT576)， 價差NT279元.降幅32.63%'),
    (14, '五、911935Y 藍芽喇叭  供應商: 威騰 進貨價:  CNY361.8 (NT1628.1)'),
    (15, '        新供應商: 科莱德912792Y 進貨單價議決 CNY300 (NT1350)， 價差NT278.1元.降幅17.08%'),
    (16, '六、模具與開發費用：CNY188,100  (NT846,450)【開發費用CNY96,000、模具費CNY92,100】'),
    (17, '       1.模具費：塑膠面殼、塑膠底蓋、矽膠按鍵、防水密封圈模具CNY92,100(NT415,450)'),
    (18, '                    交貨達15,000台，返還模具費CNY92,100，另藍芽喇叭開發與模具費CNY10,000科萊德承擔'),
    (19, '       2.開發費：開發費用CNY146,000，科萊德承擔CNY50,000，TGB承擔CNY96,000'),
    (20, '        分二期給付：1.合約簽訂時 T/T給付50% CNY94,050 (NT423,225)'),
    (21, '                                 2.初樣合格 T/T給付50% CNY94,050 (NT423,225)'),
    (22, '七、初樣送樣數量: 付款啟動合約4個月內交付各3PCS(不付費)'),
    (23, '八、認證：CE→33,000、R10→36,000與FCC→24,000，認證費用小計 93,000 於啟動與獲證各50%T/T給付'),
    (24, '九、付款方式：FOB 深圳港'),
    (25, '        1.前5批量產預付貨款30% T/T給付.尾款70% T/T給付款到發貨。'),
    (26, '        2.第6批起依據船公司裝貨日期(提單日期)起計算 L/C 60天'),
    (27, '十、最低訂購量: 300pcs'),
    (28, '十一、前置期: 45天'),
    (29, '十二、合約書一式二份 併呈請鈞長用印.'),
    (30, '             -----------------   以           上  -----------------------'),
    (31, '         呈   核   示'),
]

for row_idx, text in content_rows:
    merge_cells(table, row_idx, 1, row_idx, 15)
    is_header = row_idx in [30, 31]
    sz = 11 if not is_header else 11
    bld = row_idx == 31
    set_cell(table.cell(row_idx, 1), text, bold=bld, size=sz, align='center' if row_idx == 30 else 'left')

# Signature area (rows 33-38) - merged columns per Excel
merge_cells(table, 33, 1, 38, 1)   # col 1
merge_cells(table, 33, 2, 38, 5)   # cols 2-5
merge_cells(table, 33, 6, 38, 6)   # col 6
merge_cells(table, 33, 7, 38, 10)  # cols 7-10
merge_cells(table, 33, 11, 38, 11) # col 11
merge_cells(table, 33, 12, 38, 14) # cols 12-14

# Signature labels
set_cell(table.cell(33, 1), '副總經理：', size=11, align='center')
set_cell(table.cell(33, 2), '開發部：', size=11, align='center')
set_cell(table.cell(33, 6), '', size=11, align='center')
set_cell(table.cell(33, 7), '營業部：', size=11, align='center')
set_cell(table.cell(33, 11), '', size=11, align='center')
set_cell(table.cell(33, 12), '', size=11, align='center')

# Row 38: bottom merged across 1-16 (0-indexed: 1-16)
merge_cells(table, 38, 1, 38, 16)

# Save
output_path = r'C:\260728-code\sign-template\中控議決簽呈模板_完整版.docx'
doc.save(output_path)
print('完整版 Word 檔已建立:', output_path)