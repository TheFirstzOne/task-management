import os
import winshell
from win32com.client import Dispatch

# ตำแหน่งไฟล์ .exe (เวอร์ชันเร็ว - Multiple Files)
exe_path = os.path.join(os.getcwd(), "dist", "JobDiary", "JobDiary.exe")

# ตำแหน่ง Desktop
desktop = winshell.desktop()

# ชื่อ shortcut
shortcut_name = "บันทึกการทำงานรายวัน.lnk"
shortcut_path = os.path.join(desktop, shortcut_name)

# ตำแหน่งไอคอน
icon_path = os.path.join(os.getcwd(), "job_diary_icon.ico")

# สร้าง shortcut
shell = Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.TargetPath = exe_path
shortcut.WorkingDirectory = os.path.dirname(exe_path)
shortcut.IconLocation = icon_path
shortcut.Description = "โปรแกรมบันทึกการทำงานรายวัน"
shortcut.save()

print(f"สร้าง shortcut สำเร็จที่: {shortcut_path}")
print(f"ชี้ไปที่: {exe_path}")
