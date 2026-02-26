

# แผนปรับปรุงหน้าจัดการหน่วยงาน (Agency Management)

## สรุปภาพรวม
เปลี่ยนหน้า `/agencies` จากหน้าแสดงผลอย่างเดียว ให้เป็นระบบ CRUD เต็มรูปแบบ พร้อมรองรับโปรโตคอล MCP, A2A, API และสามารถทดสอบการเชื่อมต่อได้จริงผ่าน mock endpoint

---

## 1. สร้างตาราง `agencies` ในฐานข้อมูล

สร้างตารางเก็บข้อมูลหน่วยงานแทนการใช้ mock data อย่างเดียว

| Column | Type | Notes |
|--------|------|-------|
| id | uuid (PK) | auto-gen |
| name | text | ชื่อเต็ม |
| short_name | text | ชื่อย่อ |
| logo | text | emoji/URL |
| connection_type | text | 'MCP', 'A2A', 'API' |
| status | text | 'active', 'inactive' |
| description | text | |
| data_scope | text[] | |
| total_calls | integer | default 0 |
| color | text | |
| endpoint_url | text | URL ปลายทางของหน่วยงาน |
| api_key_name | text (nullable) | ชื่อ secret สำหรับ API key |
| created_at | timestamptz | default now() |
| updated_at | timestamptz | default now() |

- RLS policies: public read/insert/update/delete (ตามรูปแบบเดิมที่ยังไม่มี auth)
- Seed ข้อมูล 4 หน่วยงานเริ่มต้นลงตาราง
- Enable realtime สำหรับตารางนี้

---

## 2. สร้าง Edge Function `agency-manage`

Backend function สำหรับ CRUD + ทดสอบการเชื่อมต่อ

- **GET** (list): ดึงรายการหน่วยงานทั้งหมดจากตาราง
- **POST** (create): เพิ่มหน่วยงานใหม่
- **PUT** (update): แก้ไขข้อมูลหน่วยงาน
- **DELETE**: ลบหน่วยงาน
- **POST with action=test**: ทดสอบการเชื่อมต่อ โดย:
  - **MCP**: จำลองการส่ง MCP handshake (mock response สำเร็จ)
  - **API**: จำลองการเรียก REST endpoint (mock health check)
  - **A2A**: จำลองการส่ง Agent Card exchange (mock response)

---

## 3. ปรับปรุง `useAgencies` hook

- เปลี่ยนจากดึง mock data มาเป็นดึงจากตาราง `agencies` โดยตรงผ่าน Supabase client
- เพิ่ม mutation functions: `createAgency`, `updateAgency`, `deleteAgency`, `testConnection`
- Subscribe realtime เพื่ออัปเดตอัตโนมัติ

---

## 4. ปรับปรุง UI หน้า AgenciesPage

### 4.1 หน้าหลัก
- เพิ่มปุ่ม "เพิ่มหน่วยงาน" ด้านบน
- แต่ละ card มีปุ่ม: แก้ไข, ลบ, ทดสอบการเชื่อมต่อ
- ปุ่มทดสอบแสดงผลลัพธ์ (สำเร็จ/ล้มเหลว) พร้อม response time
- Badge แสดง connection type (MCP/A2A/API) พร้อมสีแยกตามประเภท

### 4.2 Dialog เพิ่ม/แก้ไขหน่วยงาน
- Form fields: ชื่อ, ชื่อย่อ, โลโก้ (emoji picker), คำอธิบาย, ประเภทการเชื่อมต่อ (MCP/A2A/API), endpoint URL, ขอบเขตข้อมูล (tag input), สี
- Validation ด้วย zod
- แสดงคำอธิบายสั้นๆ ของแต่ละโปรโตคอลเมื่อเลือก

### 4.3 Dialog ยืนยันการลบ
- AlertDialog ยืนยันก่อนลบ

### 4.4 Connection Test Panel
- เมื่อกดทดสอบ แสดง step-by-step animation:
  1. กำลังเชื่อมต่อ...
  2. ส่ง handshake/request...
  3. ได้รับการตอบกลับ
  4. ผลลัพธ์: สำเร็จ/ล้มเหลว + response time

---

## 5. อัปเดต Sidebar และ ai-chat orchestrator

- Sidebar: ดึงรายการหน่วยงานจากตารางแทน mock data
- ai-chat: อัปเดต `agencies-list` edge function ให้ดึงจากตารางแทน hardcode

---

## รายละเอียดทางเทคนิค

### ไฟล์ที่สร้างใหม่
- `supabase/migrations/xxx_create_agencies_table.sql` - สร้างตาราง + seed data
- `supabase/functions/agency-manage/index.ts` - CRUD + test endpoint
- `src/components/agencies/AgencyFormDialog.tsx` - Form dialog สำหรับเพิ่ม/แก้ไข
- `src/components/agencies/ConnectionTestResult.tsx` - แสดงผลทดสอบการเชื่อมต่อ
- `src/components/agencies/DeleteAgencyDialog.tsx` - ยืนยันการลบ

### ไฟล์ที่แก้ไข
- `src/hooks/useAgencies.ts` - เปลี่ยนเป็น CRUD + realtime
- `src/pages/AgenciesPage.tsx` - เพิ่ม UI สำหรับ CRUD + test
- `src/types/agency.ts` - เพิ่ม fields ใหม่ (endpoint_url, api_key_name, updated_at)
- `src/components/layout/AppSidebar.tsx` - ดึงจาก hook แทน mock
- `supabase/functions/agencies-list/index.ts` - ดึงจากตาราง

### ลำดับการทำงาน
1. สร้างตาราง agencies + seed data
2. อัปเดต types
3. สร้าง edge function `agency-manage`
4. อัปเดต `useAgencies` hook
5. สร้าง UI components (form, delete dialog, test result)
6. ปรับปรุง AgenciesPage
7. อัปเดต Sidebar และ agencies-list function

