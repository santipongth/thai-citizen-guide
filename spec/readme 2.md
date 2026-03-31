# OneChat API

Base URL: http://localhost:8000
Base URL: http://185.84.160.55:10540/v1/chat

---

## POST /v1/chat

รับคำถามจากผู้ใช้และส่งคืนคำตอบที่สังเคราะห์จากหน่วยงานภาครัฐที่เกี่ยวข้อง

### Request

json
{
  "query": "ยาพาราเซตามอลต้องขึ้นทะเบียนอย่างไร",
  "mcp_endpoint_url": "https://mcp.example.com/catalog"
}

| Field | Type | Required | Description |
|---|---|---|---|
| query | string | required | คำถามจากผู้ใช้ (whitespace จะถูก normalize อัตโนมัติ) |
| mcp_endpoint_url | string (URL) | required | URL ของ MCP Catalog สำหรับค้นหาหน่วยงาน |

Field ที่ไม่รองรับจะถูกปฏิเสธด้วย 400 error


---

### Response 200

json
{
  "data": {
    "answer": "### คำตอบ\nการขึ้นทะเบียนยาต้องยื่นเอกสาร...",
    "agencies": [
      {
        "id": "fda",
        "name": "สำนักงาน อย.",
        "relevance_score": 0.95,
        "query": "ขั้นตอนการขึ้นทะเบียนยาพาราเซตามอล"
      }
    ],
    "errors": []
  },
  "meta": {
    "intent": "search",
    "synthesized": true,
    "responseTimeMs": 3420
  }
}

**data** — เนื้อหาคำตอบ

| Field | Type | Description |
|---|---|---|
| data.answer | string | คำตอบในรูปแบบ Markdown หรือข้อความ fallback หากทุกหน่วยงาน fail |
| data.agencies | array | หน่วยงานที่ถูก query สำเร็จ |
| data.agencies[].id | string | Agency ID |
| data.agencies[].name | string | ชื่อหน่วยงาน |
| data.agencies[].relevance_score | float \| null | คะแนนความเกี่ยวข้อง 0.0–1.0 |
| data.agencies[].query | string \| null | คำถามที่ส่งไปยังหน่วยงานนี้ |
| data.errors | array | รายละเอียด error จากหน่วยงานที่ fail |

**meta** — ข้อมูล processing

| Field | Type | Description |
|---|---|---|
| meta.intent | "search" \| "chitchat" | ประเภทคำถาม |
| meta.synthesized | boolean | true = LLM สังเคราะห์จาก agencies / false = ตอบตรง |
| meta.responseTimeMs | integer | เวลาประมวลผลรวม (milliseconds) |

---

### Response 400

json
{ "error": "Missing query parameter" }

เกิดขึ้นเมื่อ:
- ไม่มี query หรือ query เป็น string ว่าง / whitespace ล้วน
- mcp_endpoint_url ไม่ใช่ URL ที่ถูกต้อง
- ส่ง field ที่ไม่รองรับ

---

## GET /health

json
{ "status": "ok" }

---

## Behavior ที่ควรรู้

| กรณี | data.answer | meta.synthesized | data.errors |
|---|---|---|---|
| สำเร็จปกติ | คำตอบสังเคราะห์ | true | [] |
| chitchat (เช่น "สวัสดี") | คำตอบตรงจาก LLM | false | [] |
| บางหน่วยงาน fail | ตอบจากหน่วยงานที่สำเร็จ | true | มี error บางส่วน |
| ทุกหน่วยงาน fail | "ไม่สามารถดึงข้อมูลได้..." | false | มี error ทั้งหมด |

data.answer จะมีค่าเสมอ — ไม่มี null/empty กลับมา

---

## Examples

### คำถามทั่วไป

bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "โอนที่ดินต้องเสียภาษีอะไรบ้าง",
    "mcp_endpoint_url": "https://mcp.example.com/catalog"
  }'

json
{
  "data": {
    "answer": "### ภาษีการโอนที่ดิน\n...",
    "agencies": [
      {"id": "land", "name": "กรมที่ดิน", "relevance_score": 0.92, "query": "ขั้นตอนการโอนที่ดิน"},
      {"id": "revenue", "name": "กรมสรรพากร", "relevance_score": 0.88, "query": "ภาษีที่ต้องชำระเมื่อโอนที่ดิน"}
    ],
    "errors": []
  },
  "meta": {"intent": "search", "synthesized": true, "responseTimeMs": 4210}
}

### Chitchat

bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "สวัสดี", "mcp_endpoint_url": "https://mcp.example.com/catalog"}'

json
{
  "data": {"answer": "สวัสดีครับ มีอะไรให้ช่วยไหม?", "agencies": [], "errors": []},
  "meta": {"intent": "chitchat", "synthesized": false, "responseTimeMs": 620}
}

### Health Check

bash
curl http://localhost:8000/health