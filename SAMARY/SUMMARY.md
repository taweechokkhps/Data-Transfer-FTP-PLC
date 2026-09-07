# สรุปโปรเจกต์ Keyence PLC Data Transfer FTP (v1.1.0)

> สำหรับเอกสารฉบับเต็มอย่างละเอียด สามารถดูได้ที่: [PROJECT_SUMMARY.md](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/SAMARY/PROJECT_SUMMARY.md)

---

### สรุปย่อใจความสำคัญ (v1.1.0 Modular Clean Architecture)

1. **วัตถุประสงค์:**
   - โปรแกรมดึงข้อมูล Log การผลิตจากเครื่อง Keyence PLC ผ่านเครือข่าย FTP อัตโนมัติและแบบ Manual
   - คัดแยกโฟลเดอร์ตามชื่อเครื่อง PLC, ชื่อกระบวนการ (`MC1 Connector Leak`, `MC2 Final And Resistance`, `MC3 Auto Appearance`) และแยกตามวันที่ (`DD-MM-YYYY`)

2. **สิ่งที่เพิ่มใหม่ในเวอร์ชันนี้ (v1.1.0):**
   - **📁 Remote FTP Folder Browser:** ปุ่มสำรวจและเลือกโฟลเดอร์บน PLC โดยตรงในหน้า Add/Edit PLC
   - **🛡️ Auto Path Sanitizer:** แปลง `\` เป็น `/` และตัด `C:` หรือชื่อไดรฟ์ออกอัตโนมัติ ไม่เกิด Error 550 อีกต่อไป
   - **🏗️ Modular Architecture:** แยกโค้ดเป็น `core/` (Services, Logic) และ `ui/` (Views, Components) สะอาดและเป็นระเบียบ
   - **📝 Persistent File Logger:** บันทึก Log ลง `logs/app.log` ตรวจสอบย้อนหลังได้
   - **⚡ Incremental Download:** ข้ามไฟล์ที่มีขนาดตรงกับบนเครื่องปลายทางแล้ว ไม่ต้องโหลดซ้ำ

3. **โครงสร้างไฟล์สำคัญ:**
   - [`main.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/main.py): จุดเริ่มรันระบบ
   - [`core/ftp_service.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/core/ftp_service.py): เชื่อมต่อ, สำรวจโฟลเดอร์ และดาวน์โหลด FTP
   - [`core/path_utils.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/core/path_utils.py): จัดการ Path FTP และ Local Directory
   - [`core/logger.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/core/logger.py): ระบบ Log กลาง
   - [`core/config_service.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/core/config_service.py): คอนฟิกและค่าเริ่มต้น
   - [`ui/app.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/ui/app.py): หน้าต่างหลักธีมสีม่วง
   - [`ui/views/`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/ui/views/): หน้า Dashboard, PLC Manager, Settings
   - [`ui/components/`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/ui/components/): FTPBrowserDialog, LogConsole, Tooltip
