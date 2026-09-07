# เอกสารสรุปภาพรวมโปรเจกต์ (Project Summary)
## Keyence PLC Data Transfer FTP (FTP Control) - v1.1.0

> **บันทึกเอกสารเมื่อ:** 7 กันยายน 2026 (ปรับปรุงเป็น v1.1.0 Modular Architecture)  
> **ที่ตั้งโปรเจกต์:** `C:\Users\user\Desktop\Data Transfer FTP\Data Transfer FTP`  
> **ไฟล์สรุปนี้จัดเก็บที่:** `C:\Users\user\Desktop\Data Transfer FTP\Data Transfer FTP\SAMARY\PROJECT_SUMMARY.md`

---

## 1. ภาพรวมโปรเจกต์ (Project Overview)

**Keyence PLC Data Transfer FTP** (ชื่อโปรแกรมใน UI: *FTP Get Data Record Process Critical Control* หรือ *FTP Control*) เป็นโปรแกรม Desktop Application ที่พัฒนาด้วยภาษา **Python** ร่วมกับ **CustomTkinter** โดยมีวัตถุประสงค์เพื่อ:
1. **เชื่อมต่อและดึงไฟล์ข้อมูลการผลิต (Process Data / Log Files)** เช่น ไฟล์นามสกุล `.csv`, `.txt` จากการ์ดหน่วยความจำของเครื่อง **Keyence PLC** ผ่านโปรโตคอล **FTP** (File Transfer Protocol)
2. **ระบบเลือกโฟลเดอร์บน FTP (Remote FTP Folder Browser):** สำรวจและเลือกโฟลเดอร์บน PLC ได้ด้วยการกดปุ่ม Browse ไม่ต้องพิมพ์ Path เอง
3. **ระบบแปลงและทำความสะอาด Path อัตโนมัติ (Auto Path Sanitizer):** ป้องกันข้อผิดพลาด (เช่น Error 550 จากการเผลอใส่ Path แบบ Windows `C:\...` หรือ `\`) โดยแปลงเป็นรูปแบบ FTP ที่ถูกต้องให้อัตโนมัติ
4. **จัดระเบียบโครงสร้างการจัดเก็บไฟล์บนเครื่องคอมพิวเตอร์ให้อัตโนมัติ:** แยกโฟลเดอร์ตามชื่อเครื่อง PLC, ชื่อกระบวนการ/เครื่องจักรย่อย (MC) และแยกตามวันที่บันทึก (`DD-MM-YYYY`)
5. **ระบบดึงข้อมูลอัตโนมัติตามรอบเวลา (Auto Pull Scheduler):** ตั้งความถี่รอบการดึงไฟล์ในระดับนาที พร้อมตัวนับถอยหลัง (Cooldown Timer)
6. **ระบบบันทึก Log ลงไฟล์อัตโนมัติ (Persistent Logger):** มีการเขียน Log ลงไฟล์ `logs/app.log` เพื่อให้ตรวจสอบปัญหาย้อนหลังได้
7. **ความสะดวกในการใช้งานแบบพกพา (Standalone Executable):** คอมไพล์เป็นไฟล์ `.exe` ตัวเดียว (`FTP_Control.exe`) ด้วย **Nuitka** นำไปเปิดใช้งานบนเครื่อง Windows ใดๆ ได้ทันทีโดยไม่ต้องลง Python

---

## 2. โครงสร้างไฟล์และโฟลเดอร์ของโปรเจกต์ (Project Structure)

```text
C:\Users\user\Desktop\Data Transfer FTP\Data Transfer FTP\
│
├── SAMARY\                         # เก็บเอกสารสรุปโครงการ
│   ├── PROJECT_SUMMARY.md          # เอกสารสรุปฉบับเต็ม (ไฟล์นี้)
│   └── SUMMARY.md                  # เอกสารสรุปย่อ
│
├── core/                           # เลเยอร์ Business Logic & Services
│   ├── __init__.py
│   ├── path_utils.py               # ตัวจัดการและกรอง Path FTP / Local Directory
│   ├── ftp_service.py              # ตัวเชื่อมต่อ FTP, ดาวน์โหลด และสำรวจโฟลเดอร์
│   ├── config_service.py           # จัดการอ่าน/เขียนบันทึกการตั้งค่าลง config.json
│   └── logger.py                   # ระบบ Log กลาง (ส่ง UI Console + บันทึกลง logs/app.log)
│
├── ui/                             # เลเยอร์ Graphical User Interface (CustomTkinter)
│   ├── __init__.py
│   ├── app.py                      # หน้าต่างหลัก Navigation Sidebar และระบบ Theme
│   ├── components/
│   │   ├── __init__.py
│   │   ├── tooltip.py              # วิดเจ็ต Tooltip แสดงคำแนะนำเมื่อชี้เมาส์
│   │   ├── log_console.py          # กล่องข้อความ Log Console แยกสี พร้อมปุ่ม Clear
│   │   └── ftp_browser_dialog.py   # หน้าต่าง Modal เลือกโฟลเดอร์บนเครื่อง PLC
│   └── views/
│       ├── __init__.py
│       ├── dashboard_view.py       # หน้า Overview, การ์ดแสดง PLC, ปุ่มดึงไฟล์, Cooldown
│       ├── plc_manager_view.py     # หน้า PLC Manager พร้อมปุ่ม Test และ Browse FTP
│       └── settings_view.py        # หน้า Settings เลือกโฟลเดอร์ นามสกุล และรอบเวลา
│
├── tests/                          # ชุดทดสอบ Unit Tests
│   ├── test_path_utils.py          # ทดสอบ Path Sanitizer
│   ├── test_config_and_logger.py   # ทดสอบ ConfigManager และ AppLogger
│   └── test_ftp_service.py         # ทดสอบการเชื่อมต่อและสำรวจโฟลเดอร์ FTP
│
├── main.py                         # จุดเริ่มต้นรันโปรแกรม (Entry Point)
├── config.json                     # ไฟล์เก็บคอนฟิก
├── requirements.txt                # ไลบรารีที่จำเป็น (customtkinter, imageio)
├── build.bat                       # สคริปต์ Nuitka Build ตัวเต็ม
├── build_quick.bat                 # สคริปต์ Nuitka Build ด่วน
├── FTP_Control.exe                 # ไฟล์โปรแกรมที่ Compile สำเร็จแล้ว
│
├── app_icon.ico                    # ไอคอนโปรแกรมสำหรับไฟล์ .exe (Windows Icon)
├── app_icon.png                    # ไอคอนโปรแกรมสำหรับแสดงผลบนหน้าต่าง GUI
├── README.md                       # คู่มือการใช้งานเบื้องต้น
│
├── gui.py                          # Compatibility shim -> ui.app
├── ftp_client.py                   # Compatibility shim -> core.ftp_service
└── config_manager.py               # Compatibility shim -> core.config_service
```

---

## 3. สถาปัตยกรรมและการทำงานของแต่ละโมดูล (Module Architecture)

### 3.1 `core/path_utils.py`
- **`sanitize_remote_path(path_str)`**:
  - ตัดช่องว่างหน้า-หลัง
  - แปลง Backslash `\` เป็น Forward Slash `/`
  - ตัด Windows Drive Letters (เช่น `C:`, `D:`) ออกอัตโนมัติ เพื่อป้องกัน FTP Error 550
  - จัดการเครื่องหมาย Slash ซ้ำซ้อนให้เหลือชั้นเดียว
- **`format_local_save_dir(...)`**:
  - จัดการสร้างโฟลเดอร์ปลายทางบนคอมพิวเตอร์อย่างปลอดภัยผ่าน `pathlib.Path`

### 3.2 `core/ftp_service.py`
- **`test_connection(...)`**: ฟังก์ชันทดสอบการเชื่อมต่อไปยัง PLC ด้วย timeout 5 วินาที
- **`list_remote_directories(...)`**: ฟังก์ชันสำรวจโฟลเดอร์ย่อยใน Path ที่กำหนดบน FTP Server สำหรับระบบ FTP Browser
- **`FTPDownloader`**: คลาสจัดการดาวน์โหลดไฟล์:
  - เชื่อมต่อและดักจับข้อความ Debug Log
  - ตรวจสอบขนาดไฟล์ก่อนดาวน์โหลด หากขนาดตรงกันจะข้ามเพื่อประหยัดเวลา (Incremental check)
  - แมปโฟลเดอร์ต้นทางเข้ากับชื่อเครื่องจักร (`MC1 Connector Leak`, `MC2 Final And Resistance`, `MC3 Auto Appearance`)
  - มีฟังก์ชัน `stop()` เพื่อยกเลิกอย่างปลอดภัย

### 3.3 `core/config_service.py`
- จัดการอ่าน/เขียนไฟล์ `config.json` มีระบบ Default Fallback และ Data Migration

### 3.4 `core/logger.py`
- ซิงเกิลตัน `AppLogger` กระจายข้อความ Log ไปยังหน้าจอ UI (แยกแท็ก error / warning / success) พร้อมทั้งเขียนลงไฟล์ `logs/app.log` หมุนเวียนขนาดไม่เกิน 5MB

### 3.5 `ui/components/ftp_browser_dialog.py`
- หน้าต่างสำรวจโฟลเดอร์บน FTP:
  - มีช่อง Address Bar พร้อมปุ่ม **⬆ Up** เพื่อถอยกลับโฟลเดอร์แม่
  - แสดงรายการโฟลเดอร์ทั้งหมด ดับเบิลคลิกเพื่อเข้าสู่โฟลเดอร์ย่อย
  - กดปุ่ม **Select This Directory** เพื่อนำ Path ไปใส่ในหน้าต่างตั้งค่า PLC อัตโนมัติ

---

## 4. สรุปผลการปรับปรุง (Refactoring Summary)

| รายการเดิม (v1.0.0) | ปรับปรุงใหม่ (v1.1.0) | ประโยชน์ที่ได้รับ |
|---|---|---|
| โค้ด UI ทั้งหมดรวมอยู่ใน `gui.py` ไฟล์เดียว 500 บรรทัด | แยกเป็นโมดูลย่อยใน `ui/views/` และ `ui/components/` | อ่านง่าย แยกความรับผิดชอบชัดเจน แก้ไขจุดใดไม่กระทบจุดอื่น |
| ผู้ใช้พิมพ์ Path ผิดทำให้เกิด Error 550 (เช่น ใส่ `C:\...`) | มี `sanitize_remote_path()` แปลงและตัด Path อัตโนมัติ | ไม่เกิด Error 550 จากรูปแบบ Path อีกต่อไป |
| ต้องเดาหรือจำชื่อโฟลเดอร์บน PLC | มีปุ่ม **📁 Browse FTP...** ให้คลิกเลือกโฟลเดอร์ได้โดยตรง | ใช้งานสะดวก รวดเร็ว แม่นยำ 100% |
| Log หายเมื่อปิดโปรแกรม | มี `core/logger.py` บันทึกลง `logs/app.log` | ตรวจสอบข้อผิดพลาดหรือเหตุการณ์ย้อนหลังได้ |
| ดาวน์โหลดไฟล์ซ้ำทุกครั้ง | มีการเช็คขนาดไฟล์ก่อนดาวน์โหลด | ประหยัดเวลาและ Bandwidth เครือข่าย |
