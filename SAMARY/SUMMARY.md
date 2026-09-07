# สรุปโปรเจกต์ Keyence PLC Data Transfer FTP

> สำหรับเอกสารฉบับเต็มอย่างละเอียด สามารถดูได้ที่: [PROJECT_SUMMARY.md](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/SAMARY/PROJECT_SUMMARY.md)

---

### สรุปย่อใจความสำคัญ (Quick Overview)

1. **วัตถุประสงค์:**
   - โปรแกรมดึงข้อมูล Log การผลิตจากเครื่อง Keyence PLC ผ่านเครือข่าย FTP อัตโนมัติและแบบ Manual
   - คัดแยกโฟลเดอร์ตามชื่อเครื่อง PLC, ชื่อกระบวนการ (`MC1 Connector Leak`, `MC2 Final And Resistance`, `MC3 Auto Appearance`) และแยกตามวันที่ (`DD-MM-YYYY`)

2. **ไฟล์หลักในระบบ:**
   - [`main.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/main.py): จุดเริ่มรันระบบ
   - [`gui.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/gui.py): หน้าต่างโปรแกรม (CustomTkinter) ธีมสีม่วง Dark Mode มีหน้า Overview, PLC Manager, Settings
   - [`ftp_client.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/ftp_client.py): ระบบเชื่อมต่อ FTP, ดาวน์โหลด และคัดแยกโฟลเดอร์
   - [`config_manager.py`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/config_manager.py): จัดการบันทึกการตั้งค่าลง `config.json`
   - [`build.bat`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/build.bat) / [`build_quick.bat`](file:///C:/Users/user/Desktop/Data%20Transfer%20FTP/Data%20Transfer%20FTP/build_quick.bat): สคริปต์คอมไพล์เป็น `FTP_Control.exe` ผ่าน Nuitka

3. **คุณสมบัติเด่น:**
   - ตั้งรอบเวลา Auto Pull (เช่น ทุก 60 นาที) พร้อม Cooldown timer นับถอยหลังบนหน้าจอ
   - ทดสอบการเชื่อมต่อ (🔌 Test Connection) รายเครื่องได้ทันที
   - คอนโซล Log แสดงสถานะแบบแยกสี (เขียว = สำเร็จ, แดง = ผิดพลาด, ส้ม = เตือน)
   - ใช้งานแบบ Standalone `.exe` ไม่ต้องติดตั้ง Python บนเครื่องปลายทาง
