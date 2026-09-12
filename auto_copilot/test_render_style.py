import os
from PIL import Image, ImageDraw, ImageFont

img = Image.open('auto_copilot/frame_orig_5s.png').convert('RGBA')
draw = ImageDraw.Draw(img)

# Font setup
try:
    font_sub_spk = ImageFont.truetype('C:\\Windows\\Fonts\\msyhbd.ttc', 28)
    font_sub_txt = ImageFont.truetype('C:\\Windows\\Fonts\\msyhbd.ttc', 26)
except:
    font_sub_spk = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 28)
    font_sub_txt = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 26)

# Test transparent subtitle at bottom (NO background box!)
sub_y = 1010
spk = '👨‍🔧 Technician: '
txt = '"AutoCopilot, check vehicle health status and active DTCs."'

# Draw with black outline (stroke_width=3, stroke_fill=(10, 15, 25))
draw.text((160, sub_y), spk, font=font_sub_spk, fill=(0, 230, 255), stroke_width=3, stroke_fill=(10, 15, 25))
spk_w = draw.textlength(spk, font=font_sub_spk)
draw.text((160 + spk_w, sub_y + 1), txt, font=font_sub_txt, fill=(255, 215, 0), stroke_width=3, stroke_fill=(10, 15, 25))

img.save('auto_copilot/test_sub_transparent.png')
print('Transparent subtitle test saved!')
