# เอกสารสรุปภาพรวมโปรเจกต์ (Project Summary)
## Keyence PLC Data Transfer FTP (FTP Control)

> **บันทึกเอกสารเมื่อ:** 7 กันยายน 2026  
> **ที่ตั้งโปรเจกต์:** `C:\Users\user\Desktop\Data Transfer FTP\Data Transfer FTP`  
> **ไฟล์สรุปนี้จัดเก็บที่:** `C:\Users\user\Desktop\Data Transfer FTP\Data Transfer FTP\SAMARY\PROJECT_SUMMARY.md`

---

## 1. ภาพรวมโปรเจกต์ (Project Overview)

**Keyence PLC Data Transfer FTP** (ชื่อโปรแกรมใน UI: *FTP Get Data Record Process Critical Control* หรือ *FTP Control*) เป็นโปรแกรม Desktop Application ที่พัฒนาด้วยภาษา **Python** ร่วมกับ **CustomTkinter** โดยมีวัตถุประสงค์เพื่อ:
1. **เชื่อมต่อและดึงไฟล์ข้อมูลการผลิต (Process Data / Log Files)** เช่น ไฟล์นามสกุล `.csv`, `.txt` จากการ์ดหน่วยความจำของเครื่อง **Keyence PLC** ผ่านโปรโตคอล **FTP** (File Transfer Protocol)
2. **จัดระเบียบโครงสร้างการจัดเก็บไฟล์บนเครื่องคอมพิวเตอร์ให้อัตโนมัติ** โดยสามารถแยกโฟลเดอร์ตามชื่อเครื่อง PLC, ชื่อกระบวนการ/เครื่องจักรย่อย (MC) และแยกตามวันที่บันทึก (`DD-MM-YYYY`)
3. **ระบบดึงข้อมูลอัตโนมัติตามรอบเวลา (Auto Pull Scheduler)** ที่สามารถตั้งความถี่รอบการดึงไฟล์ในระดับนาที พร้อมตัวนับถอยหลัง (Cooldown Timer) แสดงบนหน้าจอ
4. **ความสะดวกในการใช้งานแบบพกพา (Standalone Executable)** สามารถคอมไพล์เป็นไฟล์ `.exe` ตัวเดียว (`FTP_Control.exe`) ด้วย **Nuitka** นำไปเปิดใช้งานบนเครื่อง Windows ใดๆ ได้ทันทีโดยไม่ต้องลง Python

---

## 2. โครงสร้างไฟล์และโฟลเดอร์ของโปรเจกต์ (Project Structure)

```text
C:\Users\user\Desktop\Data Transfer FTP\Data Transfer FTP\
│
├── SAMARY\                         # [โฟลเดอร์นี้] เก็บเอกสารสรุปโครงการ
│   └── PROJECT_SUMMARY.md          # ไฟล์สรุปภาพรวมการทำงานและคู่มือทั้งหมด
│
├── main.py                         # จุดเริ่มต้นรันโปรแกรม (Entry Point)
├── gui.py                          # ส่วนติดต่อผู้ใช้ (Graphical User Interface)
├── ftp_client.py                   # ตัวจัดการการเชื่อมต่อและดาวน์โหลดไฟล์ผ่าน FTP
├── config_manager.py               # จัดการอ่าน/เขียนบันทึกการตั้งค่าลง config.json
├── config.json                     # ไฟล์เก็บคอนฟิก (Global Settings & รายชื่อ PLC)
│
├── requirements.txt                # ไลบรารีที่จำเป็นสำหรับพัฒนา (customtkinter, imageio)
├── build.bat                       # สคริปต์ Nuitka Build ตัวเต็ม (ลง lib + compile exe)
├── build_quick.bat                 # สคริปต์ Nuitka Build ด่วน (compile exe ทันที)
├── FTP_Control.exe                 # ไฟล์โปรแกรมที่ Compile สำเร็จแล้ว พร้อมใช้งาน
│
├── app_icon.ico                    # ไอคอนโปรแกรมสำหรับไฟล์ .exe (Windows Icon)
├── app_icon.png                    # ไอคอนโปรแกรมสำหรับแสดงผลบนหน้าต่าง GUI
├── README.md                       # คู่มือการใช้งานเบื้องต้น
│
├── venv\                           # Python Virtual Environment (Python 3.9)
├── main.build\                     # โฟลเดอร์ Cache ชั่วคราวจากการ Build ของ Nuitka
├── main.dist\                      # โฟลเดอร์ผลลัพธ์การ Build
└── main.onefile-build\             # โฟลเดอร์แคชการสร้างไฟล์แบบ Onefile
```

---

## 3. สถาปัตยกรรมและการทำงานของแต่ละโมดูล (Module Architecture)

### 3.1 `main.py`
- ทำหน้าที่เป็น Entry point สั้นๆ สำหรับเปิดโปรแกรม
- เรียกคลาส `App()` จาก `gui.py` และสั่ง `app.mainloop()`

### 3.2 `config_manager.py` (Config Management)
- **คลาส `ConfigManager`**:
  - โหลดและบันทึกข้อมูลการตั้งค่าลงในไฟล์ `config.json`
  - มีค่า Default Configuration อัตโนมัติหากยังไม่มีไฟล์
  - รองรับ CRUD สำหรับ PLC (`add_plc`, `update_plc`, `delete_plc`)
  - ฟังก์ชัน `update_global_settings` สำหรับบันทึกการตั้งค่าส่วนกลาง
  - มี Migration Logic เพื่อล้างคีย์เก่าที่ไม่ใช้แล้ว (เช่น ลบฟิลด์ `"group"` ออกอัตโนมัติ)

**โครงสร้างข้อมูลใน `config.json`:**
```json
{
    "global_settings": {
        "target_directory": "D:/Data_Logs",
        "file_extensions": [".csv", ".txt"],
        "separate_by_date": true,
        "auto_pull_interval_minutes": 60
    },
    "plcs": [
        {
            "name": "Line 1 PLC",
            "host": "192.168.0.10",
            "port": 21,
            "username": "ftp",
            "password": "",
            "remote_directory": "/0_CARD/log0/,/0_CARD/log1/,/0_CARD/log2/"
        }
    ]
}
```

### 3.3 `ftp_client.py` (FTP Engine)
- **คลาส `FTPDownloader`**:
  - จัดการเชื่อมต่อ FTP โดยใช้ไลบรารีมาตรฐาน `ftplib` ของ Python
  - ดักจับ Debug Log ของ FTP ผ่าน `redirect_stdout` เพื่อรายงานข้อความแจ้งเตือนที่ละเอียด (เช่น Error 530 เมื่อรหัสผ่านผิดพลาด)
  - **การจับคู่นามสกุลไฟล์:** กรองเฉพาะไฟล์ที่มีนามสกุลตรงกับ `file_extensions`
  - **การจับคู่โฟลเดอร์ต้นทางกับเครื่องจักร (Machine Mapping):**
    - เมื่อกำหนด `remote_directories` แบบคั่นด้วยเครื่องหมายจุลภาค (comma `,`)
    - ไดเรกทอรีลำดับที่ 1 จะถูกจัดเก็บเข้าโฟลเดอร์: `MC1 Connector Leak`
    - ไดเรกทอรีลำดับที่ 2 จะถูกจัดเก็บเข้าโฟลเดอร์: `MC2 Final And Resistance`
    - ไดเรกทอรีลำดับที่ 3 จะถูกจัดเก็บเข้าโฟลเดอร์: `MC3 Auto Appearance`
    - ไดเรกทอรีลำดับถัดไปจะตั้งชื่อเป็น `MC{index}`
  - **โครงสร้างการบันทึกไฟล์ปลายทาง (Local Directory Structure):**
    ```text
    {TargetFolder}/
    └── {PLC_Name}/
        ├── MC1 Connector Leak/
        │   └── 07-09-2026/
        │       └── DATA001.CSV
        ├── MC2 Final And Resistance/
        │   └── 07-09-2026/
        │       └── DATA002.CSV
        └── MC3 Auto Appearance/
            └── 07-09-2026/
                └── DATA003.CSV
    ```
  - รองรับ Callback Function เพื่ออัปเดตเปอร์เซ็นต์ Progress Bar (`progress_callback`) และข้อความ Log Console (`log_callback`) แบบ Real-time
  - มีฟังก์ชัน `stop()` เพื่อยกเลิกการดาวน์โหลดอย่างปลอดภัย

### 3.4 `gui.py` (Graphical User Interface)
- ใช้ **CustomTkinter** แบบ **Dark Mode** คุมโทนสีม่วง (`#7B1FA2`, `#4A148C`)
- ประกอบด้วย 3 หน้าต่างหลัก (เมนูด้านซ้าย):
  1. **Overview (Dashboard)**:
     - แสดงการ์ดรายการของแต่ละ PLC
     - ปุ่ม **🔌 Test Connection**: ยิงคำสั่งทดสอบเชื่อมต่อ FTP ใน Thread แยก พร้อมแสดงสถานะ (`Testing...`, `Conn OK`, `Conn Fail`)
     - แสดง Progress Bar และจำนวนไฟล์ที่ดึงเสร็จ (`Current/Total`)
     - ปุ่ม **Download** ประจำแต่ละ PLC
     - ปุ่ม **Download All** ด้านล่าง สำหรับสั่งดึงข้อมูลจากทุก PLC พร้อมกัน
     - ข้อความนับถอยหลัง **Cooldown Timer** (เช่น `Next Auto Pull in: 45:12`)
     - **Log Console** หน้าต่างแสดงผลข้อความการทำงาน แยกสีชัดเจน:
       - สีแดง: ข้อความ Error / Failure
       - สีส้ม: ข้อความ Warning
       - สีเขียว: ข้อความ Success / Completed
  2. **PLC Manager**:
     - หน้าจัดการ เพิ่ม/แก้ไข/ลบ PLC
     - ตารางแสดง Name, Host:Port, Username, Remote Directories
     - มีหน้าต่าง Modal Dialog สำหรับระบุค่าต่าง ๆ
  3. **Settings**:
     - เลือก Target Save Directory ผ่านระบบเลือกโฟลเดอร์ Windows (Folder Browser)
     - กำหนดนามสกุลไฟล์ที่ต้องการ เช่น `.csv, .txt`
     - สวิตช์ Checkbox เปิด/ปิด การแยกโฟลเดอร์ตามวันที่ (`separate_by_date`)
     - กำหนดช่วงเวลาดึงอัตโนมัติ (นาที) หรือใส่ `0` หากต้องการปิด

---

## 4. ระบบเบื้องหลังสำคัญ (Key Internal Mechanisms)

1. **การทำงานแบบ Multi-threading:**
   - การทดสอบการเชื่อมต่อและการดาวน์โหลดไฟล์ถูกรันบน `threading.Thread(daemon=True)` ทั้งหมด ทำให้หน้าต่างโปรแกรมไม่ค้าง (Non-blocking GUI) ขณะรอดาวน์โหลดไฟล์ขนาดใหญ่หรือรอเชื่อมต่อ Network
2. **ระบบ Auto Pull & Cooldown Loop:**
   - ใช้ `self.after(interval_ms, ...)` ของ Tkinter เพื่อรันงานตามรอบเวลาโดยไม่บล็อก Event Loop
   - ฟังก์ชัน `update_cooldown_ui` คำนวณเวลาที่เหลือเป็นวินาทีและอัปเดตข้อความ `Next Auto Pull in: MM:SS` ทุก ๆ 1 วินาที
   - เมื่อผู้ใช้กดปุ่ม Download All ด้วยตนเอง ตัวจับเวลาจะถูกรีเซ็ตใหม่ทันทีเพื่อป้องกันการดาวน์โหลดซ้ำซ้อน
3. **การ Bundle ทรัพยากรสำหรับ Executable:**
   - ฟังก์ชัน `resource_path()` รองรับการอ่านรูปไอคอนจากโฟลเดอร์ชั่วคราว `sys._MEIPASS` ของ Nuitka/PyInstaller

---

## 5. การติดตั้ง พัฒนา และคอมไพล์โปรแกรม (Build & Compilation Guide)

### 5.1 สภาพแวดล้อม (Environment)
- พัฒนาบน **Python 3.9** (แนะนำเวอร์ชัน 3.9-3.11 เพื่อความเสถียรสูงสุดของ Nuitka และ Tkinter)
- มี Virtual Environment ติดตั้งไว้แล้วที่โฟลเดอร์ `venv`

### 5.2 ไลบรารีที่จำเป็น (`requirements.txt`)
```text
customtkinter==5.2.2
imageio
```

### 5.3 การคอมไพล์เป็นไฟล์ .exe (Nuitka Build)
ไฟล์ `build.bat` และ `build_quick.bat` ได้เตรียมคำสั่งสำหรับแพ็กเกจโปรแกรมไว้ดังนี้:
```bat
python -m nuitka --onefile ^
  --output-filename=FTP_Control.exe ^
  --enable-plugin=tk-inter ^
  --include-data-dir=venv\Lib\site-packages\customtkinter=customtkinter ^
  --windows-console-mode=disable ^
  --windows-icon-from-ico=app_icon.ico ^
  --include-data-files=app_icon.png=app_icon.png ^
  main.py
```
- `--onefile`: รวบรวมโปรแกรมทั้งหมดให้อยู่ในไฟล์ `.exe` เพียงไฟล์เดียว
- `--enable-plugin=tk-inter`: ดึงเอาชุด Tcl/Tk สำหรับ CustomTkinter มาใส่ในตัว build
- `--include-data-dir=...`: แนบไฟล์ assets ของ customtkinter (json themes, icons) เข้าไปด้วย
- `--windows-console-mode=disable`: ซ่อนหน้าต่าง CMD สีดำตอนเปิดโปรแกรม
- `--windows-icon-from-ico=app_icon.ico`: กำหนดไอคอนให้ไฟล์ exe บน Windows

---

## 6. ข้อแนะนำและแนวทางการพัฒนาต่อยอด (Future Improvements)

1. **การตั้งค่าชื่อเครื่องจักรแบบ Dynamic (Custom Machine Name Mapping):**
   - ปัจจุบันชื่อ `MC1 Connector Leak`, `MC2 Final And Resistance`, `MC3 Auto Appearance` ถูกกำหนดไว้แบบค่าคงที่ใน `ftp_client.py` (บรรทัดที่ 107-111)
   - *ข้อเสนอแนะ:* สามารถปรับปรุงให้ผู้ใช้งานสามารถตั้งชื่อโฟลเดอร์ของแต่ละ Directory ได้โดยตรงจากหน้าต่าง PLC Manager
2. **ระบบป้องกันการดาวน์โหลดไฟล์ซ้ำ (Incremental Download / Hash / Timestamp Check):**
   - ปัจจุบันโปรแกรมจะโหลดไฟล์ทั้งหมดที่ตรงตามนามสกุลมาเขียนทับไฟล์เดิม
   - *ข้อเสนอแนะ:* สามารถเพิ่มการตรวจสอบขนาดไฟล์หรือวันที่แก้ไข (Modification Time) เพื่อดาวน์โหลดเฉพาะไฟล์ที่เพิ่มใหม่หรือมีการเปลี่ยนแปลง
3. **การบันทึก Log ลงไฟล์ภายนอก (Persistent File Logging):**
   - เพิ่มการเขียนข้อความ log ลงในไฟล์ `app.log` หรือแยกตามวัน เพื่อให้ตรวจสอบย้อนหลังได้ในกรณีเกิดข้อผิดพลาดในการดึงข้อมูลยามค่ำคืน
4. **ดาวน์โหลดแบบแยก Thread ตามเครื่อง PLC:**
   - ปัจจุบันการกด Download All จะวนลูปสั่งดาวน์โหลดทีละ PLC ผ่าน UI button invoke
   - *ข้อเสนอแนะ:* สามารถใช้ `ThreadPoolExecutor` เพื่อดาวน์โหลดหลายๆ PLC พร้อมกันได้อย่างอิสระ
