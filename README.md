# Keyence PLC Data Transfer FTP - คู่มือการใช้งาน

โปรแกรมนี้ใช้สำหรับดึงไฟล์ข้อมูลจาก Keyence PLC ผ่านโปรโตคอล FTP โดยมี UI ที่สวยงาม ทันสมัย และสามารถตั้งค่าการดึงไฟล์แบบแยกโฟลเดอร์ตามวันที่ได้อัตโนมัติ

## 🚀 ความต้องการของระบบ (System Requirements)
- ระบบปฏิบัติการ Windows (64-bit แนะนำ)
- เชื่อมต่อ Network วงเดียวกับ PLC

---

## 📖 วิธีการใช้งานโปรแกรม

### 1. การตั้งค่าเบื้องต้น (Global Settings)
ไปที่เมนู **Global Settings** (แถบเมนูด้านซ้าย)
- **Target Save Directory:** เลือกโฟลเดอร์ปลายทางในคอมพิวเตอร์ของคุณที่จะใช้เก็บไฟล์ที่ดึงมาจาก PLC
- **File Extensions:** กำหนดนามสกุลไฟล์ที่ต้องการดึง เช่น `.csv, .txt` (คั่นด้วยลูกน้ำ)
- **Separate by Date:** หากเปิดใช้งาน โปรแกรมจะสร้างโฟลเดอร์เป็นวันที่ (เช่น `2026-08-18`) ไว้ข้างใน Target Directory อัตโนมัติ

### 2. การเพิ่ม/ลบ PLC (PLC Manager)
ไปที่เมนู **PLC Manager**
- กดปุ่ม **Add New PLC** 
- **PLC Name:** ชื่อเรียกเครื่อง PLC เช่น "Machine 1"
- **IP Address:** ไอพีของ PLC เช่น `192.168.0.10`
- **Username / Password:** รหัสผ่าน FTP ของ PLC (ปกติมักใช้ `ftp` และรหัสผ่านว่างเปล่า ขึ้นอยู่กับการตั้งค่า PLC ของคุณ)
- **Remote Directory:** โฟลเดอร์ใน PLC ที่ต้องการดึงไฟล์ (เช่น `/` หรือ `/DATA`)

### 3. การดึงไฟล์ (Dashboard)
ไปที่เมนู **Dashboard**
- คุณจะเห็นรายชื่อ PLC ทั้งหมดที่ตั้งค่าไว้
- กดปุ่ม **Download** ที่ PLC แต่ละเครื่อง เพื่อเริ่มดึงไฟล์ทันที
- แถบ Progress จะแสดงสถานะการดึงไฟล์ พร้อม Log ด้านล่างที่จะบอกว่าไฟล์ไหนถูกดึงมาบ้าง

---

## 🛠 สำหรับนักพัฒนา (Developer Guide)

โค้ดชุดนี้ถูกออกแบบและรันได้ดีที่สุดบน **Python 3.9** (เนื่องจากเวอร์ชัน 3.14 อาจจะใหม่เกินไปและมีปัญหากับบางไลบรารี)

### การจำลองสภาพแวดล้อม (Virtual Environment)
โปรแกรมถูกสร้าง Environment ไว้ให้แล้วในโฟลเดอร์ `venv` 
หากต้องการเริ่มพัฒนาต่อ ให้ใช้คำสั่ง:
```cmd
# เข้าใช้งาน venv (Windows)
.\venv\Scripts\activate

# ติดตั้งไลบรารีที่จำเป็น
pip install -r requirements.txt
pip install nuitka
```

### การแพ็คโปรแกรมเป็น .exe ด้วย Nuitka
หากต้องการส่งโปรแกรมนี้ให้ผู้ใช้งานคนอื่น โดยไม่ต้องติดตั้ง Python สามารถรันสคริปต์ `build.bat` ที่ผมเตรียมไว้ให้ได้เลย 

คำสั่งในการแพ็ค (อยู่ใน `build.bat`):
```cmd
.\venv\Scripts\activate
pip install nuitka customtkinter
nuitka --standalone --onefile --enable-plugin=tk-inter --include-data-dir=.\venv\Lib\site-packages\customtkinter=customtkinter --windows-console-mode=disable main.py
```
> **หมายเหตุ:** `nuitka` จะทำการรวบรวมไลบรารีทั้งหมด (รวมถึง customtkinter) ให้อยู่ในไฟล์ `main.exe` ไฟล์เดียว ซึ่งอาจจะใช้เวลา Build ประมาณ 2-5 นาที
