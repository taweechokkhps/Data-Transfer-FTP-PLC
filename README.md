# Keyence PLC Data Transfer FTP - คู่มือการใช้งาน (v1.1.0)

โปรแกรมนี้ใช้สำหรับดึงไฟล์ข้อมูลจาก Keyence PLC ผ่านโปรโตคอล FTP โดยมี UI ที่สวยงาม ทันสมัย รองรับการเลือกโฟลเดอร์บน FTP ผ่านระบบ Browse และสามารถตั้งค่าการดึงไฟล์แบบแยกโฟลเดอร์ตามวันที่ได้อัตโนมัติ

## 🚀 คุณสมบัติเด่น (Key Features - v1.1.0)
- **Modular Clean Architecture:** โครงสร้างโค้ดแบบแยกเลเยอร์ (`core/` และ `ui/`) อ่านง่าย บำรุงรักษาสะดวก
- **📁 Remote FTP Folder Browser:** ปุ่มสำรวจโฟลเดอร์บนเครื่อง PLC โดยตรงในหน้า Add/Edit PLC ไม่ต้องเดาหรือพิมพ์ Path เอง
- **🛡️ Auto Path Sanitizer:** ระบบทำความสะอาด Path อัตโนมัติ (แปลง Backslash `\` เป็น `/` และตัด Windows Drive Letter `C:` ออกอัตโนมัติ ป้องกัน Error 550)
- **⚡ Incremental File Transfer:** ตรวจสอบขนาดไฟล์ก่อนดาวน์โหลด หากมีไฟล์เดิมขนาดตรงกันอยู่แล้วจะข้ามอัตโนมัติ ประหยัดเวลาและ Bandwidth
- **📝 Persistent Logging:** บันทึกประวัติการทำงานและข้อผิดพลาดลงไฟล์ `logs/app.log` หมุนเวียนอัตโนมัติ
- **⏱️ Auto Pull Scheduler:** ตั้งรอบเวลาดาวน์โหลดอัตโนมัติ พร้อมตัวนับถอยหลัง Cooldown บนหน้า Dashboard

---

## 📖 วิธีการใช้งานโปรแกรม

### 1. การตั้งค่าเบื้องต้น (Settings)
ไปที่เมนู **Settings** (แถบเมนูด้านซ้าย)
- **Target Save Directory:** เลือกโฟลเดอร์ปลายทางในคอมพิวเตอร์ของคุณที่จะใช้เก็บไฟล์ที่ดึงมาจาก PLC
- **File Extensions:** กำหนดนามสกุลไฟล์ที่ต้องการดึง เช่น `.csv, .txt` (คั่นด้วยลูกน้ำ)
- **Separate by Date:** หากเปิดใช้งาน โปรแกรมจะสร้างโฟลเดอร์เป็นวันที่ (เช่น `07-09-2026`) ไว้ข้างใน Target Directory อัตโนมัติ
- **Auto Pull Interval (Minutes):** ตั้งเวลารอบการดึงอัตโนมัติเป็นนาที (ใส่ `0` หากต้องการปิด)

### 2. การเพิ่ม/แก้ไข PLC (PLC Manager)
ไปที่เมนู **PLC Manager**
- กดปุ่ม **Add New PLC** 
- **PLC Name:** ชื่อเรียกเครื่อง PLC เช่น "Line 1"
- **IP Address (Host):** ไอพีของ PLC เช่น `192.168.0.10`
- **Port:** พอร์ต FTP (ปกติคือ `21`)
- **Username / Password:** รหัสผ่าน FTP ของ PLC (ปกติมักใช้ `ftp` และรหัสผ่านว่างเปล่า)
- **Remote Directory:** สามารถกดปุ่ม **📁 Browse FTP...** เพื่อเปิดหน้าต่างเลือกโฟลเดอร์บน PLC ได้โดยตรง หรือใส่ Path เอง เช่น `/Documents/Projects/...` หรือ `/0_CARD/log0/`
- สามารถกดปุ่ม **🔌 Test Connection** เพื่อทดสอบเชื่อมต่อก่อนกดบันทึกได้ทันที

### 3. การดึงไฟล์ (Overview / Dashboard)
ไปที่เมนู **Overview**
- คุณจะเห็นรายชื่อ PLC ทั้งหมดที่ตั้งค่าไว้
- กดปุ่ม **Download** ที่ PLC แต่ละเครื่อง เพื่อเริ่มดึงไฟล์ทันที หรือกดปุ่ม **Download All** เพื่อดึงทุกเครื่อง
- แถบ Progress จะแสดงสถานะการดึงไฟล์ พร้อม Log Console ด้านล่างแบบแยกสี และมีปุ่ม **Clear** สำหรับล้างหน้าต่าง Log

---

## 🛠 สำหรับนักพัฒนา (Developer Guide)

### โครงสร้างโปรเจกต์ (Project Structure)
```text
├── main.py                     # Entry point (เรียก ui.app)
├── config.json                 # การตั้งค่าระบบ
│
├── core/                       # เลเยอร์ Core Logic & Services
│   ├── path_utils.py           # Path sanitization & local dir formatting
│   ├── ftp_service.py          # FTP connection, folder exploration & downloader
│   ├── config_service.py       # ConfigManager CRUD
│   └── logger.py               # Central logger (UI callback + file log)
│
├── ui/                         # เลเยอร์ Graphical User Interface
│   ├── app.py                  # หน้าต่างหลัก Navigation & Theme
│   ├── components/             # Tooltip, LogConsole, FTPBrowserDialog
│   └── views/                  # DashboardView, PLCManagerView, SettingsView
│
├── gui.py                      # Compatibility shim
├── ftp_client.py               # Compatibility shim
└── config_manager.py           # Compatibility shim
```

### การรันโปรแกรมในโหมดพัฒนา
```cmd
# ติดตั้งไลบรารี
pip install customtkinter imageio

# รันโปรแกรม
python main.py
```

### การแพ็คโปรแกรมเป็น .exe ด้วย Nuitka
สามารถดับเบิลคลิกไฟล์ `build.bat` หรือ `build_quick.bat` ได้ทันที  
ผลลัพธ์จะได้ไฟล์ `FTP_Control.exe` ในโฟลเดอร์โปรเจกต์
