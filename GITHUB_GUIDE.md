# คู่มือการอัปโหลดโปรเจคขึ้น GitHub

## สารบัญ
1. [สิ่งที่ต้องเตรียม](#1-สิ่งที่ต้องเตรียม)
2. [ติดตั้งและตั้งค่า Git](#2-ติดตั้งและตั้งค่า-git)
3. [สร้าง GitHub Account](#3-สร้าง-github-account)
4. [สร้าง Repository บน GitHub](#4-สร้าง-repository-บน-github)
5. [เริ่มต้น Git ในโปรเจค](#5-เริ่มต้น-git-ในโปรเจค)
6. [สร้าง .gitignore](#6-สร้าง-gitignore)
7. [Commit โค้ด](#7-commit-โค้ด)
8. [เชื่อมต่อและ Push ขึ้น GitHub](#8-เชื่อมต่อและ-push-ขึ้น-github)
9. [การ Push ครั้งต่อไป](#9-การ-push-ครั้งต่อไป)
10. [คำสั่ง Git ที่ใช้บ่อย](#10-คำสั่ง-git-ที่ใช้บ่อย)

---

## 1. สิ่งที่ต้องเตรียม

- **Git** — โปรแกรมสำหรับจัดการ version control
- **GitHub Account** — บัญชีสำหรับเก็บโค้ดบน cloud
- **Terminal / Command Prompt** — สำหรับรันคำสั่ง

---

## 2. ติดตั้งและตั้งค่า Git

### 2.1 ติดตั้ง Git
ดาวน์โหลดได้จาก https://git-scm.com/downloads แล้วติดตั้งตามขั้นตอนปกติ

ตรวจสอบว่าติดตั้งสำเร็จ:
```bash
git --version
# ผลลัพธ์: git version 2.xx.x
```

### 2.2 ตั้งค่าข้อมูลผู้ใช้ (ทำครั้งเดียว)
Git ต้องการชื่อและ email เพื่อบันทึกว่าใครเป็นคน commit

```bash
git config --global user.name "ชื่อของคุณ"
git config --global user.email "email@example.com"
```

ตรวจสอบว่าตั้งค่าถูกต้อง:
```bash
git config --global --list
```

---

## 3. สร้าง GitHub Account

1. ไปที่ https://github.com
2. คลิก **Sign up**
3. กรอก username, email, password
4. ยืนยัน email ที่ได้รับ

---

## 4. สร้าง Repository บน GitHub

Repository (repo) คือพื้นที่เก็บโค้ดบน GitHub

### ขั้นตอน:
1. Login เข้า GitHub แล้วคลิก **"+"** มุมบนขวา → **"New repository"**
   หรือไปที่ https://github.com/new

2. กรอกข้อมูล:
   - **Repository name** — ชื่อโปรเจค เช่น `my-project`
   - **Description** — คำอธิบาย (ไม่บังคับ)
   - **Public / Private** — เลือกตามต้องการ

3. **สำคัญ:** อย่าเลือก "Add a README file", "Add .gitignore" หรือ "Choose a license"
   เพราะเราจะสร้างเองจากเครื่อง

4. คลิก **"Create repository"**

5. GitHub จะแสดงหน้า repo ว่างพร้อม URL ในรูปแบบ:
   ```
   https://github.com/username/repo-name.git
   ```
   ให้เก็บ URL นี้ไว้ใช้ในขั้นตอนถัดไป

---

## 5. เริ่มต้น Git ในโปรเจค

เปิด Terminal แล้วไปยังโฟลเดอร์โปรเจค:

```bash
cd "C:\Users\YourName\Desktop\MyProject"
```

สร้าง Git repository ในโฟลเดอร์นี้:

```bash
git init
```

ผลลัพธ์:
```
Initialized empty Git repository in C:/Users/.../MyProject/.git/
```

> คำสั่งนี้สร้างโฟลเดอร์ `.git` ซ่อนอยู่ในโปรเจค ซึ่งเป็นที่เก็บ history ทั้งหมด

---

## 6. สร้าง .gitignore

`.gitignore` คือไฟล์ที่บอก Git ว่าไม่ต้องติดตามไฟล์ไหน เช่น ไฟล์ชั่วคราว, venv, ไฟล์ build

สร้างไฟล์ชื่อ `.gitignore` ในโฟลเดอร์โปรเจค แล้วใส่รายการที่ต้องการยกเว้น

**ตัวอย่างสำหรับโปรเจค Python:**
```
# Python
__pycache__/
*.pyc
*.pyo

# Virtual Environment
venv/
env/

# Build output
build/
dist/
*.exe

# Database
*.db
*.sqlite

# OS files
.DS_Store
Thumbs.db

# IDE settings
.vscode/
.idea/
```

> **เคล็ดลับ:** สร้าง `.gitignore` ก่อน `git add` เพื่อไม่ให้ไฟล์ที่ไม่ต้องการถูกเพิ่มเข้าไป

---

## 7. Commit โค้ด

Commit คือการบันทึก snapshot ของโค้ด ณ เวลานั้น

### 7.1 ตรวจสอบสถานะไฟล์
```bash
git status
```

ผลลัพธ์จะแสดงไฟล์ที่ยังไม่ได้ติดตาม (Untracked files)

### 7.2 เพิ่มไฟล์เข้า Staging Area
```bash
# เพิ่มทุกไฟล์
git add .

# หรือเพิ่มเฉพาะไฟล์ที่ต้องการ
git add main.py
git add app/
```

> **Staging Area** คือพื้นที่รอ commit ก่อนจะบันทึกจริง

### 7.3 ตรวจสอบอีกครั้งหลัง add
```bash
git status
```
ไฟล์ที่พร้อม commit จะแสดงเป็นสีเขียว

### 7.4 สร้าง Commit
```bash
git commit -m "Initial commit: เพิ่มโปรเจคครั้งแรก"
```

> ข้อความ commit ควรอธิบายว่าทำอะไรไป เช่น `"Fix login bug"`, `"Add calendar feature"`

---

## 8. เชื่อมต่อและ Push ขึ้น GitHub

### 8.1 เปลี่ยนชื่อ branch เป็น main
GitHub ใช้ชื่อ branch หลักว่า `main` (แทน `master` เดิม)

```bash
git branch -M main
```

### 8.2 เชื่อมต่อกับ Remote Repository
นำ URL ที่ได้จากขั้นตอน 4 มาใช้:

```bash
git remote add origin https://github.com/username/repo-name.git
```

ตรวจสอบว่าเชื่อมต่อถูกต้อง:
```bash
git remote -v
# ผลลัพธ์:
# origin  https://github.com/username/repo-name.git (fetch)
# origin  https://github.com/username/repo-name.git (push)
```

### 8.3 Push โค้ดขึ้น GitHub
```bash
git push -u origin main
```

- `-u` หมายความว่าตั้งค่า upstream ให้ครั้งเดียว ครั้งถัดไปพิมพ์แค่ `git push` ได้เลย
- ระบบจะขอ GitHub username และ password (หรือ Personal Access Token)

> **หมายเหตุ:** GitHub ไม่รับ password ปกติแล้ว ให้ใช้ **Personal Access Token** แทน
> สร้างได้ที่: GitHub → Settings → Developer settings → Personal access tokens

### 8.4 ตรวจสอบผล
เปิด browser ไปที่ `https://github.com/username/repo-name`
จะเห็นโค้ดทั้งหมดขึ้นบน GitHub แล้ว

---

## 9. การ Push ครั้งต่อไป

หลังจากแก้ไขโค้ดแล้ว ทำตามขั้นตอนนี้:

```bash
# 1. ตรวจสอบไฟล์ที่เปลี่ยนแปลง
git status

# 2. เพิ่มไฟล์ที่ต้องการ commit
git add .

# 3. สร้าง commit พร้อมข้อความอธิบาย
git commit -m "อธิบายสิ่งที่เปลี่ยนแปลง"

# 4. Push ขึ้น GitHub
git push
```

---

## 10. คำสั่ง Git ที่ใช้บ่อย

| คำสั่ง | ความหมาย |
|--------|-----------|
| `git status` | ดูสถานะไฟล์ทั้งหมด |
| `git add .` | เพิ่มทุกไฟล์เข้า staging |
| `git add <file>` | เพิ่มไฟล์เฉพาะเจาะจง |
| `git commit -m "msg"` | บันทึก commit พร้อมข้อความ |
| `git push` | อัปโหลดโค้ดขึ้น GitHub |
| `git pull` | ดึงโค้ดล่าสุดจาก GitHub |
| `git log` | ดูประวัติ commit ทั้งหมด |
| `git log --oneline` | ดูประวัติ commit แบบสั้น |
| `git diff` | ดูความแตกต่างของโค้ดที่ยังไม่ได้ add |
| `git restore <file>` | ยกเลิกการแก้ไขไฟล์ (คืนค่าเดิม) |
| `git branch` | ดูรายการ branch ทั้งหมด |
| `git checkout -b <name>` | สร้าง branch ใหม่และสลับไป |
| `git merge <branch>` | รวม branch เข้าด้วยกัน |
| `git clone <url>` | ดาวน์โหลด repository จาก GitHub |

---

## สรุปขั้นตอนแบบย่อ

```
ครั้งแรก (ทำครั้งเดียว):
─────────────────────────────────────────
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/user/repo.git
git push -u origin main

ครั้งต่อไป (ทุกครั้งที่แก้โค้ด):
─────────────────────────────────────────
git add .
git commit -m "อธิบายการเปลี่ยนแปลง"
git push
```
