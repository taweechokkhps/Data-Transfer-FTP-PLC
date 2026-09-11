# Design Spec: Clean Views & MVC Refactoring

## 1. Overview & Objectives
- **Branch:** `refactor/clean-views`
- **Objective:** ปรับปรุงโครงสร้างสถาปัตยกรรมของเลเยอร์ UI (`ui/`) โดยแยกโค้ดจัดวางหน้าจอ (Pure UI Layout) ออกจากตรรกะการทำงาน (Business Logic / Event Handlers / Threading) ตามรูปแบบ Model-View-Controller (MVC)
- **Target Experience:**
  - ไฟล์ใน `ui/views/` สั้น กระชับ อ่านเข้าใจง่ายสำหรับช่างหน้างานและนักพัฒนา
  - Popup Dialogs ถูกแยกเป็น Reusable Components ใน `ui/components/`
  - ตรรกะการดาวน์โหลด, การตรวจสอบฟอร์ม, และการบันทึกถูกแยกไปที่ `ui/controllers/`
  - หน้าตา UI พฤติกรรม และผลลัพธ์การทำงานคงเดิม 100% (Zero UI/Behavioral Regression)

---

## 2. Directory & File Decomposition

### 2.1 โฟลเดอร์ `ui/controllers/` (Logic Layer)
1. **`ui/controllers/dashboard_controller.py`**:
   - จัดการ State ของการดาวน์โหลด (`active_downloaders`, `plc_download_callbacks`, `plc_download_by_name`)
   - ควบคุมการดาวน์โหลดเดี่ยว (`download_single`) และดาวน์โหลดทั้งหมด (`download_all`)
   - จัดการวงรอบการนับเวลา (Timer loop) และ Thread ดาวน์โหลดเบื้องหลัง
   - การทดสอบการเชื่อมต่อ (`test_single_connection`)
2. **`ui/controllers/plc_manager_controller.py`**:
   - จัดการการตรวจสอบความถูกต้องของข้อมูล (Form Validation: Host, Port, Machines)
   - จัดการบันทึก/แก้ไขข้อมูล PLC ผ่าน `config_manager`
   - จัดการลบ PLC พร้อม Dialog ยืนยัน
3. **`ui/controllers/settings_controller.py`**:
   - จัดการเลือกโฟลเดอร์ปลายทาง (`askdirectory`)
   - ตรวจสอบความถูกต้องและบันทึกการตั้งค่าระบบ (`save_settings`)
   - คืนค่าเริ่มต้น (`reset_defaults`)

### 2.2 โฟลเดอร์ `ui/components/` (Dialog Components)
1. **`ui/components/quick_date_filter_dialog.py`**:
   - แยก `QuickDateFilterDialog` (CTkToplevel) ออกจาก `dashboard_view.py`
2. **`ui/components/plc_modal_dialog.py`**:
   - แยก `PLCModalDialog` (CTkToplevel ขนาด ~280 บรรทัด) ออกจาก `plc_manager_view.py`

### 2.3 โฟลเดอร์ `ui/views/` (Pure Presentation Layer)
1. **`ui/views/dashboard_view.py`**:
   - เหลือเฉพาะโค้ดประกอบ Widget: การ์ด PLC, Status Badge, Progress Bar, Counter Label, Timer Label, Action Buttons
   - ส่งต่อ Event ของการกดปุ่มให้ `DashboardController`
2. **`ui/views/plc_manager_view.py`**:
   - เหลือเฉพาะโค้ดวาดรายการ PLC Cards และปุ่ม "Add New PLC"
   - ส่งต่อการเปิด Dialog และการลบให้ Controller
3. **`ui/views/settings_view.py`**:
   - เหลือเฉพาะโค้ดจัดวางแบบฟอร์มช่องกรอก (Entry, Checkbox, Slider)
   - ส่งต่อการกดบันทึก/เลือกโฟลเดอร์ให้ Controller

---

## 3. Interfaces & Dependency Management
- **Thread Safety:** Controller ใช้งาน `safe_after` ของ View ในการส่งค่ากลับมาอัปเดต Widget บน Main Thread
- **Decoupling:** View ไม่เรียก `FTPDownloader` หรือ `check_omron_machine_bit` โดยตรง แต่เรียกผ่าน Controller

---

## 4. Verification Plan
1. **Controller Unit Tests (`tests/test_controllers.py`):**
   - ทดสอบ Logic ของ Controller เช่น การตรวจสอบความถูกต้องฟอร์ม, การจัดคิว Trigger, การบันทึก Config โดยไม่ต้องรัน Mainloop ของ GUI
2. **Full Regression Test Suite:**
   - รันชุดทดสอบทั้งหมด (`python -m unittest discover -s tests`) ต้องผ่าน 100%
3. **Smoke Verification:**
   - รันโปรแกรมจริง (`python main.py`) ตรวจสอบการแสดงผลทั้ง 3 แท็บ (Overview, PLC Manager, Settings) ว่าทำงานสมบูรณ์เหมือนเดิมทุกประการ
