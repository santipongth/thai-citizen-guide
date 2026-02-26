

# Clean Code, Refactor และสร้าง Mockup APIs

## ภาพรวม

Refactor โปรเจคให้แบ่งโครงสร้างชัดเจนระหว่าง Frontend และ Backend โดยสร้าง Supabase Edge Functions เป็น Mockup APIs สำหรับ 4 หน่วยงาน พร้อม Frontend service layer เรียกใช้งาน

---

## 1. Refactor Frontend - แยกโครงสร้างไฟล์ให้ชัดเจน

### 1.1 แยก Types ออกจาก Mock Data ✅
- ✅ สร้าง `src/types/agency.ts` - Agency, AgentStep types
- ✅ สร้าง `src/types/chat.ts` - ChatMessage, ConversationHistory types
- ✅ สร้าง `src/types/dashboard.ts` - DashboardStats types
- ✅ สร้าง `src/types/index.ts` - re-export ทั้งหมด

### 1.2 สร้าง API Service Layer ✅
- ✅ สร้าง `src/services/agencyApi.ts` - ฟังก์ชันเรียก Edge Functions ของแต่ละหน่วยงาน
- ✅ สร้าง `src/services/chatApi.ts` - ฟังก์ชันส่งคำถามและรับคำตอบ
- ✅ สร้าง `src/services/dashboardApi.ts` - ฟังก์ชันดึงสถิติ
- ✅ สร้าง `src/services/historyApi.ts` - ฟังก์ชันดึงประวัติสนทนา

### 1.3 สร้าง Custom Hooks ✅
- ✅ สร้าง `src/hooks/useChat.ts` - แยก chat logic ออกจาก ChatPage และ PublicPortal ให้ใช้ร่วมกัน
- ✅ สร้าง `src/hooks/useAgencies.ts` - React Query hook ดึงข้อมูลหน่วยงาน
- ✅ สร้าง `src/hooks/useDashboard.ts` - React Query hook ดึงสถิติ
- ✅ สร้าง `src/hooks/useChatHistory.ts` - React Query hook ดึงประวัติสนทนา

### 1.4 Refactor Pages ✅
- ✅ `ChatPage.tsx` - ใช้ `useChat` hook แทน logic ที่ซ้ำกัน
- ✅ `PublicPortal.tsx` - ใช้ `useChat` hook เช่นกัน ลด code ซ้ำ
- ✅ แยก Landing section เป็น `LandingHero.tsx`, `AgencyCards.tsx`, `SuggestedQuestions.tsx`

---

## 2. Backend - สร้าง Mockup APIs (Supabase Edge Functions) ✅

สร้าง Edge Functions deploy บน Lovable Cloud:

### 2.1 `agency-fda` ✅ - API จำลองสำนักงาน อย.
### 2.2 `agency-revenue` ✅ - API จำลองกรมสรรพากร
### 2.3 `agency-dopa` ✅ - API จำลองกรมการปกครอง
### 2.4 `agency-land` ✅ - API จำลองกรมที่ดิน
### 2.5 `ai-chat` ✅ - API Orchestrator หลัก (เรียก agency functions แบบ parallel, synthesize คำตอบ)
### 2.6 `dashboard-stats` ✅ - API ดึงสถิติ Dashboard
### 2.7 `agencies-list` ✅ - API ดึงรายการหน่วยงาน
### 2.8 `chat-history` ✅ - API ดึงประวัติสนทนา (รองรับ search + filter)

---

## 3. เชื่อม Frontend กับ Backend ✅

### 3.1 ปรับ `useChat` hook ✅
- ✅ เรียก `ai-chat` Edge Function แทน mock data
- ✅ แสดง agent steps แบบ real-time ตาม response
- ✅ Fallback กลับไปใช้ mock data ถ้า API ไม่พร้อม

### 3.2 Supabase Client ✅
- ✅ `src/integrations/supabase/client.ts` พร้อมใช้งาน (auto-generated)

---

## 4. UI Enhancements ✅

- ✅ เพิ่ม Markdown rendering (react-markdown + prose styling) ให้ AI responses แสดงตาราง, bold, list สวยงาม
- ✅ ทดสอบ multi-agency orchestration (เช่น คำถามที่เกี่ยวข้อง FDA + Revenue พร้อมกัน)

---

## สถานะโดยรวม: ✅ เสร็จสมบูรณ์ทุกข้อ

### ไฟล์ทั้งหมดที่สร้าง/แก้ไข
| ไฟล์ | สถานะ |
|---|---|
| `src/types/agency.ts`, `chat.ts`, `dashboard.ts`, `index.ts` | ✅ |
| `src/services/agencyApi.ts`, `chatApi.ts`, `dashboardApi.ts`, `historyApi.ts` | ✅ |
| `src/hooks/useChat.ts`, `useAgencies.ts`, `useDashboard.ts`, `useChatHistory.ts` | ✅ |
| `src/components/public/LandingHero.tsx`, `AgencyCards.tsx`, `SuggestedQuestions.tsx` | ✅ |
| `src/components/chat/MessageBubble.tsx` (markdown rendering) | ✅ |
| `supabase/functions/` (8 Edge Functions) | ✅ |
| `src/pages/` (ChatPage, PublicPortal, Dashboard, Agencies, History) | ✅ |
