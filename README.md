# PLC Data Transfer FTP - คู่มือการใช้งาน (v1.4.0)

โปรแกรมสำหรับเชื่อมต่อและดึงไฟล์ข้อมูลจากเครื่องจักรและ PLC (รองรับทั้ง **Keyence** และ **Omron**) ผ่านโปรโตคอล FTP พร้อมระบบแปลงไฟล์เป็น CSV อัตโนมัติ, ระบบความปลอดภัย FINS Interlock, คำนวณเวลาที่เหลือจริง (ETA) และวัดความเร็วการโอนถ่ายข้อมูลแบบ Real-time โดยมี UI ที่สวยงาม ทันสมัย ใช้งานง่ายในระดับโรงงานอุตสาหกรรม

---

## 🚀 คุณสมบัติเด่น (Key Features - v1.4.0)

- **🚦 Smart Concurrency & Per-Host Queueing (v1.4.0):**
  - **คนละ IP (ต่างตู้):** ดาวน์โหลดขนานพร้อมกันทันที (Parallel) เต็มสปีด
  - **IP เดียวกัน:** ป้องกันปัญหา Socket ชนกันบน PLC โดยจัดคิวให้อัตโนมัติ (Sequential) พร้อมแสดงสถานะ `● In Queue` บนหน้า Dashboard
- **🔒 Duplicate IP & Name Prevention (v1.4.0):**
  - ตรวจจับและปฏิเสธทันทีเมื่อผู้ใช้เผลอกรอก IP Address หรือชื่อ Line ซ้ำในหน้าจอตั้งค่า ป้องกันระบบชนกันในหน้างาน
- **📁 FTP Browser Loading Guard & Auto-Scroll to Top (v1.4.0):**
  - ล็อคปุ่มเลือกโฟลเดอร์ชั่วคราว (`⏳ Loading...`) ขณะกำลังดึงข้อมูลจาก PLC ป้องกันการส่งค่าโฟลเดอร์ว่าง
  - รีเซ็ต Scrollbar ไปบนสุดเสมอเมื่อเข้าโฟลเดอร์ใหม่ ไม่ค้างตำแหน่งเดิม
- **🏗️ Decoupled Clean MVC Architecture (v1.4.0):**
  - ปรับโครงสร้างแยก Logic และ View ชัดเจนด้วย Controller และ Dialog Components เพื่อความเสถียรสูงสุด
- **⚡ Real-time Speed & Dynamic ETA Display:**
  - คำนวณเวลาที่เหลือโดยประมาณ (ETA) แบบแม่นยำจากระยะเวลาการดึงข้อมูลจริงผ่านเครือข่าย รองรับหน่วยชั่วโมง (เช่น `~1.24 Hour`), นาที (`~3 Min`) และวินาที (`~30 Sec`)
  - แสดงความเร็วในการดาวน์โหลดจริงแบบสดๆ (`KB/s`, `MB/s`) เช่น `150/430 (35%) • (~3 Min) • 320 KB/s`
- **🛡️ Omron FINS Safety Interlock (Port 9600 UDP):**
  - ตรวจสอบสถานะการทำงานของเครื่องจักร (บิตโหมด AUTO / MANUAL) ก่อนดาวน์โหลดไฟล์วันปัจจุบัน เพื่อป้องกันการดึงไฟล์ขณะเครื่องจักรกำลังบันทึกข้อมูล
- **📊 Auto TXT-to-CSV Conversion:**
  - แปลงไฟล์ข้อมูลดิบ (`.txt`) เป็นไฟล์ `.csv` ให้อัตโนมัติทันทีที่ดาวน์โหลดเสร็จ พร้อมแยกเก็บเป็นสัดส่วนในโฟลเดอร์ `csv/` และ `plaintext/`
- **🏭 Multi-Machine Support ต่อ 1 PLC:**
  - รองรับการตั้งค่าเครื่องจักรย่อยหลายเครื่อง (เช่น MC1, MC2, MC3) ภายใต้การ์ดควบคุมหรือ PLC ตัวเดียวกัน
- **📅 Smart Date Range Filtering:**
  - เลือกช่วงวันที่ที่ต้องการดึงข้อมูลย้อนหลังได้จากหน้า Dashboard ผ่านปุ่ม Calendar Badge โดยไม่ต้องไปแก้ใน Settings
- **⚡ Smart Duplicate File Skip:**
  - ตรวจสอบไฟล์ในอดีตที่ปิดรอบไปแล้ว หากมีไฟล์ในเครื่องคอมพิวเตอร์ครบถ้วนแล้วจะข้ามทันที ประหยัดเวลาและลดโหลดของเครื่องจักร
  - ไฟล์ของวันปัจจุบันจะดึงมาอัปเดตให้อัตโนมัติเพื่อให้ได้ข้อมูลกะล่าสุดเสมอ
- **🌐 Dual FTP Mode & Thai Encoding Support:**
  - รองรับทั้งโหมด Passive (PASV) และ Active (PORT) พร้อมระบบสลับโหมดอัตโนมัติเมื่อ PLC ตอบกลับรหัส 502
  - รองรับรหัสภาษาไทย CP874, TIS-620 และ UTF-8 ไม่ทำให้ชื่อไฟล์ภาษาไทยเพี้ยน
- **🛑 Emergency Socket Cleanup (Industrial Grade):**
  - ระบบตัดการเชื่อมต่อและปิด Socket กับ PLC ทันทีเมื่อกดยกเลิกหรือปิดโปรแกรมกะทันหัน ป้องกันพอร์ตสื่อสารของการ์ด PLC ค้าง
- **⏱️ Auto Pull Scheduler:**
  - ตั้งรอบเวลาดาวน์โหลดอัตโนมัติ พร้อมตัวนับถอยหลัง Cooldown บนหน้า Dashboard

---

## 📖 วิธีการใช้งานโปรแกรม

### 1. การตั้งค่าเบื้องต้น (Settings)
ไปที่เมนู **Settings** (แถบเมนูด้านซ้าย)
- **Target Save Directory:** เลือกโฟลเดอร์ปลายทางในคอมพิวเตอร์ที่จะใช้บันทึกไฟล์
- **File Extensions:** กำหนดนามสกุลไฟล์ที่ต้องการดึง เช่น `.csv, .txt` (คั่นด้วยจุลภาค)
- **Separate by Date:** เปิดใช้งานหากต้องการให้โปรแกรมจัดหมวดหมู่แยกโฟลเดอร์ตามวันที่ของไฟล์
- **Auto Pull Interval (Minutes):** ตั้งเวลารอบการดึงข้อมูลอัตโนมัติ (ใส่ `0` หากต้องการปิดและใช้เฉพาะการกดมือ)

### 2. การจัดการเครื่อง PLC (PLC Manager)
ไปที่เมนู **PLC Manager**
- กดปุ่ม **Add New PLC** 
- **PLC Name:** ชื่อระบุเครื่อง เช่น "Line 1 - Robot Cell"
- **IP Address (Host):** ไอพีของ PLC เช่น `192.168.0.10`
- **Port:** พอร์ต FTP (ปกติคือ `21`)
- **Username / Password:** รหัสผ่าน FTP ของ PLC
- **FTP Mode:** เลือก `Auto`, `Passive` หรือ `Active` (ค่าเริ่มต้นแนะนำ `Auto`)
- **Machines:** กำหนดโฟลเดอร์ Remote Directory ของแต่ละเครื่องจักร เช่น `/MEMCARD/LOG/` พร้อมปุ่ม **📁 Browse FTP...** สำหรับสำรวจโฟลเดอร์จากเครื่องจริงโดยตรง
  - มีระบบ **Loading Guard** ล็อคปุ่มยืนยันชั่วคราว (`⏳ Loading...`) ขณะกำลังดึงข้อมูลจาก PLC ป้องกันการส่งค่าโฟลเดอร์ว่าง
  - มีระบบ **Auto-Scroll to Top** รีเซ็ตตำแหน่ง Scrollbar กลับไปที่ด้านบนสุดเสมอเมื่อเข้าโฟลเดอร์ใหม่
- **ระบบป้องกัน IP และชื่อซ้ำ (Duplicate Prevention):**
  - โปรแกรมจะตรวจสอบและปฏิเสธทันทีหากมีการกรอก IP Address (`host:port`) หรือชื่อ Line ซ้ำกับตู้เดิม เพื่อป้องกันปัญหาการแย่ง Socket หรือข้อมูลทับซ้อนกัน
- กดปุ่ม **🔌 Test Connection** เพื่อทดสอบว่าเชื่อมต่อและล็อกอินผ่านก่อนบันทึก

### 3. การดึงไฟล์ (Overview / Dashboard)
ไปที่เมนู **Overview**
- ดูภาพรวมสถานะของทุก PLC ในสายการผลิต
- **เลือกช่วงวันที่:** คลิกที่ป้ายวันที่ (เช่น `📅 All Files` หรือ `📅 Range`) เพื่อกำหนดช่วงวันที่ต้องการดึงข้อมูล
- **ระบบจัดคิวแยกตาม Host IP (Smart Concurrency):**
  - **ต่าง IP (คนละเครื่อง):** ดาวน์โหลดขนานพร้อมกันทันที (Parallel) เต็มสปีด
  - **IP เดียวกัน:** จัดเข้าคิวรออัตโนมัติ (Sequential) โดยการ์ดถัดไปจะแสดงสถานะ `● In Queue` พร้อมข้อความระบุว่ากำลังรอตู้ใดว่างอยู่ ป้องกัน Socket ชนกันบนบอร์ด PLC
- **เริ่มดาวน์โหลด:**
  - กดปุ่ม **⬇ Download** ที่เครื่องที่ต้องการดึงเฉพาะเครื่องนั้น
  - หรือกดปุ่ม **📥 Download All** ที่แถบด้านบน เพื่อสั่งดึงไฟล์จากทุก PLC พร้อมกัน
- **ขณะดาวน์โหลด:**
  - แถบ Progress Bar จะแสดงความคืบหน้า จำนวนไฟล์ เวลาที่เหลือ (ETA) และสปีดความเร็ว เช่น:
    ```text
    150/430 (35%) • (~3 Min) • 320 KB/s
    ```
  - นาฬิกาจับเวลา (`⏱ 00:25`) จะนับเวลาที่ใช้จริง
  - หากต้องการหยุดกลางคัน สามารถกดปุ่ม **🛑 Stop** หรือ **Stop All** เพื่อยกเลิกอย่างปลอดภัยได้ทันที (รวมถึงตู้ที่กำลังรอคิวอยู่ด้วย)
- **Log Console:** ตรวจสอบข้อความการทำงานแบบแยกสี (เขียว=สำเร็จ, ส้ม=คำเตือน, แดง=ข้อผิดพลาด)

---

## 🛠 สำหรับนักพัฒนา (Developer Guide)

### โครงสร้างโปรเจกต์ (Project Structure)
```text
├── main.py                         # จุดเริ่มต้นโปรแกรม (Entry point)
├── config.json                     # การตั้งค่า PLC และพารามิเตอร์ระบบ
├── build_nuitka.bat                # สคริปต์คอมไพล์โปรแกรมเป็น Standalone .exe ด้วย Nuitka
│
├── core/                           # เลเยอร์ Business Logic & Background Services
│   ├── path_utils.py               # ระบบจัดการ Path, ชื่อไฟล์, วันที่ และโฟลเดอร์
│   ├── ftp_service.py              # FTP Engine, ETA Calculator, Speed Estimator, Concurrency Pool
│   ├── converter_service.py        # ตัวแปลงไฟล์ TXT เป็น CSV อัตโนมัติ
│   ├── fins_service.py             # โปรโตคอล Omron FINS UDP (Port 9600) ตรวจสอบโหมดเครื่องจักร
│   ├── config_service.py           # จัดการโหลด/บันทึกการตั้งค่า (Thread-safe ConfigManager)
│   └── logger.py                   # ระบบบันทึก Log แบบรวมศูนย์ (UI Console + logs/app.log)
│
├── ui/                             # เลเยอร์ส่วนติดต่อผู้ใช้ (CustomTkinter - MVC Architecture)
│   ├── app.py                      # หน้าต่างหลัก เมนูนำทาง และ Version Badge
│   ├── controllers/                # Controller Layer: Business Logic & Concurrency Coordination
│   │   ├── dashboard_controller.py   # ควบคุมคิวดาวน์โหลด Per-Host Lock, เธรดเบื้องหลัง, ทดสอบการเชื่อมต่อ
│   │   ├── plc_manager_controller.py # จัดการ CRUD ตู้ PLC, Form Validation, ป้องกัน IP & ชื่อซ้ำ
│   │   └── settings_controller.py    # จัดการตรวจสอบและบันทึกการตั้งค่าระบบ, เลือกโฟลเดอร์ปลายทาง
│   ├── views/                      # View Layer: Pure Presentation & UI Layouts
│   │   ├── dashboard_view.py       # หน้าจอหลัก Overview แสดงการ์ดและการตอบสนองของแต่ละ Line
│   │   ├── plc_manager_view.py     # หน้าจอแสดงรายการและการ์ดของตู้ PLC
│   │   └── settings_view.py        # หน้าจอฟอร์มการตั้งค่าระบบ
│   └── components/                 # Reusable UI & Modal Components
│       ├── plc_modal_dialog.py     # โมดอลฟอร์มสำหรับเพิ่ม/แก้ไข Line PLC
│       ├── ftp_browser_dialog.py   # โมดอลสำรวจโฟลเดอร์บน PLC พร้อม Loading Guard & Auto-Scroll to Top
│       ├── quick_date_filter_dialog.py # โมดอลเลือกช่วงวันที่ดาวน์โหลดแบบด่วน
│       ├── date_picker.py          # วิดเจ็ตปฏิทินแบบกำหนดเอง
│       ├── log_console.py          # คอนโซลแสดง Log แบบ Real-time พร้อมแถบกรองสี
│       ├── modal_utils.py          # เครื่องมือคำนวณตำแหน่งและจัดการหน้าต่างโมดอล
│       └── tooltip.py              # ป๊อปอัปแสดงคำแนะนำเมื่อวางเมาส์เหนือปุ่ม
│
├── tests/                          # ชุดทดสอบ Unit & Regression Tests (52 Tests - 100% Pass)
│   ├── test_controllers.py         # ทดสอบ Controller ทุกตัว (Per-Host Queue, Duplicate IP/Name, CRUD)
│   ├── test_ftp_browser_dialog.py  # ทดสอบ Loading Guard, Control State, Auto-Scroll Top
│   ├── test_ftp_service.py         # ทดสอบการเชื่อมต่อ, ETA, Speed, Parallel Worker Pool
│   ├── test_ftp_logging.py         # ทดสอบระบบ Logging และ Debug Level
│   ├── test_converter_service.py   # ทดสอบการแปลง TXT เป็น CSV
│   ├── test_fins_service.py        # ทดสอบโปรโตคอล Omron FINS UDP
│   ├── test_config_and_logger.py   # ทดสอบ ConfigManager และ App Logger
│   ├── test_date_picker.py         # ทดสอบระบบปฏิทินและ Date Parsing
│   └── test_path_utils.py          # ทดสอบการตัดแต่ง Path และจัดโครงสร้างโฟลเดอร์
```

### การรันโปรแกรมในโหมดพัฒนา
```powershell
# ติดตั้งไลบรารีที่จำเป็น
pip install customtkinter imageio

# รันโปรแกรม
python main.py

# รันชุดทดสอบทั้งหมด (52 Unit Tests)
python -m unittest discover -s tests
```

### การคอมไพล์เป็นไฟล์ .exe (Standalone)
รันไฟล์สคริปต์ Nuitka:
```cmd
build_nuitka.bat
```
ผลลัพธ์จะได้ไฟล์ `FTP_Control.exe` ที่สามารถนำไปใช้งานบนคอมพิวเตอร์เครื่องอื่นได้ทันทีโดยไม่ต้องติดตั้ง Python
