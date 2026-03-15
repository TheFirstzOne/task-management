from PIL import Image, ImageDraw, ImageFont
import os

# สร้างไอคอนขนาด 256x256
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# วาดสมุดบันทึก (notebook)
# พื้นหลังสมุด - สีน้ำเงิน
notebook_color = (33, 150, 243)  # Blue
notebook_rect = [40, 30, 216, 226]
draw.rounded_rectangle(notebook_rect, radius=10, fill=notebook_color)

# ขอบสมุดทางซ้าย - สีเข้ม
draw.rectangle([40, 30, 55, 226], fill=(21, 101, 192))

# วาดเส้นบนสมุด (สันสมุด)
for i in range(3):
    y = 60 + i * 50
    draw.ellipse([20 + i*15, y-5, 40 + i*15, y+5], fill=(100, 100, 100))

# วาดกระดาษในสมุด - สีขาว
paper_rect = [65, 50, 206, 206]
draw.rounded_rectangle(paper_rect, radius=5, fill=(255, 255, 255))

# วาดเส้นบนกระดาษ
line_color = (200, 200, 200)
for i in range(6):
    y = 70 + i * 22
    draw.line([75, y, 196, y], fill=line_color, width=2)

# วาดปากกา/ดินสอ
pen_color = (244, 67, 54)  # Red
# ลำปากกา
pen_body = [(170, 160), (220, 210), (215, 215), (165, 165)]
draw.polygon(pen_body, fill=pen_color)
# หัวปากกา
draw.polygon([(220, 210), (215, 215), (225, 220)], fill=(100, 100, 100))

# เงาของสมุด
shadow_rect = [45, 226, 221, 232]
draw.rounded_rectangle(shadow_rect, radius=10, fill=(0, 0, 0, 50))

# บันทึกเป็นไฟล์ .ico ขนาดต่างๆ
icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
icons = []
for icon_size in icon_sizes:
    icons.append(img.resize(icon_size, Image.Resampling.LANCZOS))

# บันทึกเป็นไฟล์ .ico
icon_path = 'job_diary_icon.ico'
icons[0].save(icon_path, format='ICO', sizes=[(s[0], s[1]) for s in icon_sizes])

print(f"Icon created successfully: {icon_path}")
