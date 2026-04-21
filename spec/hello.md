# OneChat API

Base URL: http://185.84.160.55:8000

---

## POST /v1/chat

รับคำถามจากผู้ใช้และส่งคืนคำตอบที่สังเคราะห์จากหน่วยงานภาครัฐที่เกี่ยวข้อง (LLM รวมคำตอบเป็น Markdown เดียว)

### Request

{
  "query": "การทำบัตรประชาชนใหม่ต้องไปที่ไหน",
  "mcp_endpoint_url": "http://185.84.161.145/mcp",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}

| Field | Type | Required | Description |
|---|---|---|---|
| query | string | required | คำถามจากผู้ใช้ (whitespace จะถูก normalize อัตโนมัติ) |
| mcp_endpoint_url | string (URL) | required | URL ของ MCP server สำหรับค้นหาหน่วยงาน |
| session_id | string (UUID) | optional | Session ID สำหรับ multi-turn chat — ถ้าไม่ส่ง server จะสร้าง UUID ใหม่ให้ |

Field ที่ไม่รองรับจะถูกปฏิเสธด้วย 400 error


---

### Response 200

{
  "data": {
    "answer": "### การทำบัตรประชาชนใหม่\nสามารถไปติดต่อได้ที่สำนักงานเขต/อำเภอ...",
    "agencies": [
      {
        "id": "019d5cf7-9dc4-70e0-b4a5-3f549d0cf7b9",
        "name": "กรมการปกครอง",
        "endpoint_url": "https://8885-203-185-144-41.ngrok-free.app/dopa/chat",
        "relevance_score": 0.95,
        "query": "การทำบัตรประชาชนใหม่ต้องไปที่ไหน"
      },
      {
        "id": "019d5cf7-9dcf-7aa5-bc3e-21ba67822923",
        "name": "กรมที่ดิน",
        "endpoint_url": "https://8885-203-185-144-41.ngrok-free.app/dol/chat",
        "relevance_score": null,
        "query": "การทำบัตรประชาชนใหม่ต้องไปที่ไหน"
      }
    ],
    "errors": [
      {
        "agency": "019d5cf7-9dcf-7aa5-bc3e-21ba67822923",
        "name": "กรมที่ดิน",
        "errorType": "TimeoutError",
        "message": "agency timed out after 60000 ms"
      }
    ]
  },
  "meta": {
    "intent": "search",
    "synthesized": true,
    "responseTimeMs": 65420,
    "session_id": "00c958f3-dab0-4268-9451-fd0eac90ab87"
  }
}

**data**

| Field | Type | Description |
|---|---|---|
| data.answer | string | คำตอบในรูปแบบ Markdown หรือข้อความ fallback หากทุกหน่วยงาน fail |
| data.agencies | array | หน่วยงานทั้งหมดที่ถูกเลือก (รวมถึงที่ fail — ดู data.errors ประกอบ) |
| data.agencies[].id | string | Agency ID (UUID จาก MCP server) |
| data.agencies[].name | string | ชื่อหน่วยงาน |
| data.agencies[].endpoint_url | string | URL endpoint ที่ถูกเรียกจริง |
| data.agencies[].relevance_score | float \| null | คะแนนความเกี่ยวข้อง 0.0–1.0 — null หาก agency fail ก่อนถึงขั้น verify |
| data.agencies[].query | string \| null | คำถามที่ส่งไปยังหน่วยงานนี้ (ถ้ามีหลาย sub-question จะ join ด้วย newline) |
| data.errors | array | หน่วยงานที่ fail (connection error, timeout, ไม่มีคำตอบ, relevance ต่ำ) |
| data.errors[].agency | string | Agency ID ที่ fail |
| data.errors[].name | string \| null | ชื่อหน่วยงานที่ fail |
| data.errors[].errorType | string | ประเภท error เช่น ConnectError, TimeoutError, RelevanceError, EmptyAgencyAnswer |
| data.errors[].message | string | ข้อความ error |

Agency ที่ fail จะปรากฏทั้งใน `data.agencies` (score = null) และใน `data.errors` พร้อมกัน


**meta**

| Field | Type | Description |
|---|---|---|
| meta.intent | "search" \| "chitchat" | ประเภทคำถาม |
| meta.synthesized | boolean | true = LLM สังเคราะห์คำตอบ / false = ตอบตรงหรือ fail ทุกหน่วยงาน |
| meta.responseTimeMs | integer | เวลาประมวลผลรวม (milliseconds) |
| meta.session_id | string (UUID) | Session ID — echo กลับจาก request หรือ UUID ที่ server สร้างให้ |

---

### Response 400

{ "error": "Missing query parameter" }

เกิดขึ้นเมื่อ:
- ไม่มี query หรือ query เป็น string ว่าง / whitespace ล้วน
- mcp_endpoint_url ไม่ใช่ URL ที่ถูกต้อง
- ส่ง field ที่ไม่รองรับ

---

## POST /v2/chat

รับคำถามจากผู้ใช้และส่งคืนคำตอบ *แยกต่อหน่วยงาน* โดยไม่มีการสังเคราะห์ — ได้ข้อความต้นฉบับจากแต่ละหน่วยงานโดยตรง

Request body เหมือนกับ /v1/chat ทุกประการ

---

### Response 200

{
  "data": {
    "agencies": [
      {
        "id": "019d5cf7-9dc4-70e0-b4a5-3f549d0cf7b9",
        "name": "กรมการปกครอง",
        "endpoint_url": "https://8885-203-185-144-41.ngrok-free.app/dopa/chat",
        "query": "การทำบัตรประชาชนใหม่ต้องไปที่ไหน",
        "answer": "สำหรับคำถามของคุณนะคะ น้องปกป้องพบหัวข้อที่เกี่ยวข้องดังนี้ค่ะ:\n\n• **8.การขอมีบัตรประจำตัวประชาชนใหม่ กรณีบัตรเดิมหมดอายุ**\n  ดูรายละเอียดเพิ่มเติมได้ที่: https://www.dopa.go.th/public_service/service_guide47/view206\n• **9.การขอมีบัตรประจำตัวประชาชนใหม่ กรณีบัตรสูญหายหรือถูกทำลาย**\n  ดูรายละเอียดเพิ่มเติมได้ที่: https://www.dopa.go.th/public_service/service_guide47/view207",
        "relevance_score": 0.95
      },
      {
        "id": "019da1da-b3aa-7f75-bffa-9f0c59053e08",
        "name": "promes.co.th",
        "endpoint_url": "https://api.dify.promes.co.th/v1/chat-messages",
        "query": "การเสียภาษีต้องทำอย่างไร",
        "answer": "สวัสดีครับ พี่คุ้มครองจากกรมคุ้มครองสิทธิและเสรีภาพครับ...\n\n### 1. การเป็นผู้มีหน้าที่เสียภาษี\n- ผู้ที่เป็น **เจ้าของที่ดินหรือสิ่งปลูกสร้าง** ณ วันที่ 1 มกราคมของทุกปี...",
        "relevance_score": 0.82
      }
    ],
    "errors": [
      {
        "agency": "019d5cf7-9dc4-70e0-b4a5-3f549d0cf7b9",
        "name": "กรมการปกครอง",
        "errorType": "RelevanceError",
        "message": "The information provided is not relevant to your query."
      },
      {
        "agency": "019d5cf7-9dcf-7aa5-bc3e-21ba67822923",
        "name": "กรมที่ดิน",
        "errorType": "TimeoutError",
        "message": "agency timed out after 60000 ms"
      },
      {
        "agency": "019d5cf7-9dcf-7aa5-bc3e-21ba67822923",
        "name": "กรมที่ดิน",
        "errorType": "TimeoutError",
        "message": "agency timed out after 60000 ms"
      }
    ]
  },
  "meta": {
    "intent": "search",
    "synthesized": false,
    "responseTimeMs": 126113,
    "session_id": "00c958f3-dab0-4268-9451-fd0eac90ab87"
  }
}

**data**

| Field | Type | Description |
|---|---|---|
| data.agencies | array | คำตอบต้นฉบับจากทุกหน่วยงานที่ตอบสำเร็จ รวมถึงที่ relevance_score ต่ำ |
| data.agencies[].id | string | Agency ID |
| data.agencies[].name | string \| null | ชื่อหน่วยงาน |
| data.agencies[].endpoint_url | string \| null | URL endpoint ที่ถูกเรียก |
| data.agencies[].query | string \| null | คำถามที่ส่งไปยังหน่วยงานนี้ |
| data.agencies[].answer | string | ข้อความต้นฉบับที่ได้จากหน่วยงาน |
| data.agencies[].relevance_score | float \| null | คะแนนความเกี่ยวข้อง 0.0–1.0 — ไม่มีการตัดทิ้งตามคะแนน |
| data.errors | array | หน่วยงานที่ fail ก่อนตอบได้ (connection error, timeout ฯลฯ) — RelevanceError ไม่อยู่ที่นี่ |

`meta` มีโครงสร้างเหมือนกับ v1 โดย `synthesized` เป็น `false` เสมอ


---

## GET /health

{ "status": "ok" }

---

## GET /v1/mcp/agencies

ดึงรายชื่อและ configuration ของหน่วยงานทั้งหมดจาก MCP server

### Query Parameters

| Parameter | Required | Description |
|---|---|---|
| mcp_endpoint_url | required | URL ของ MCP server |

### Request

curl "http://185.84.160.55:8000/v1/mcp/agencies?mcp_endpoint_url=http://185.84.161.145/mcp"

### Response 200

คืนเป็น array โดยตรง (ไม่มี wrapper object)

[
  {
    "id": "019d5cf7-9dc4-70e0-b4a5-3f549d0cf7b9",
    "name": "กรมการปกครอง",
    "description": "ข้อมูลทะเบียนราษฎร์ บัตรประชาชน",
    "endpoint_url": "https://api.dopa.go.th/chat",
    "data_scope": ["บัตรประชาชน", "ทะเบียนบ้าน"],
    "request_query_field": "query",
    "request_static_payload": {}
  }
]

| Field | Type | Description |
|---|---|---|
| id | string | Agency ID |
| name | string | ชื่อหน่วยงาน |
| description | string \| null | คำอธิบายหน่วยงาน |
| endpoint_url | string | URL ที่ system จะเรียกจริง |
| data_scope | array | หัวข้อข้อมูลที่หน่วยงานนี้ดูแล |
| request_query_field | string | ชื่อ field ที่ใช้ส่งคำถามใน request body |
| request_static_payload | object | ค่าคงที่ที่ส่งไปพร้อมทุก request |

---

## GET /v1/mcp/health

ตรวจสอบสถานะของแต่ละหน่วยงานจาก MCP server โดยส่งคำถามทดสอบจริง

### Query Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| mcp_endpoint_url | required | — | URL ของ MCP server |
| test_query | optional | "test" | คำถามทดสอบที่ส่งไปยังแต่ละ agency |

### Request

curl "http://185.84.160.55:8000/v1/mcp/health?mcp_endpoint_url=http://185.84.161.145/mcp&test_query=สวัสดี"

### Response 200

คืนเป็น array โดยตรง (ไม่มี wrapper object)

[
  {
    "id": "019d5cf7-9dc4-70e0-b4a5-3f549d0cf7b9",
    "name": "กรมการปกครอง",
    "endpoint_url": "https://api.dopa.go.th/chat",
    "status": "online",
    "answer_preview": "สวัสดีครับ...",
    "error": null
  },
  {
    "id": "019d5cf7-9dcf-7aa5-bc3e-21ba67822923",
    "name": "กรมที่ดิน",
    "endpoint_url": "https://api.dol.go.th/chat",
    "status": "offline",
    "answer_preview": null,
    "error": "ConnectError: ..."
  }
]

| Field | Type | Description |
|---|---|---|
| id | string | Agency ID |
| name | string | ชื่อหน่วยงาน |
| endpoint_url | string | URL ที่ถูกทดสอบ |
| status | "online" \| "offline" | สถานะ |
| answer_preview | string \| null | ข้อความ 200 ตัวอักษรแรกจากคำตอบ (null ถ้า offline) |
| error | string \| null | ข้อความ error (null ถ้า online) |

---

## Multi-turn Chat (Session)

OneChat รองรับการสนทนาต่อเนื่องโดยใช้ session_id ทั้ง v1 และ v2

*วิธีใช้:*

1. Frontend สร้าง UUID ตอนเริ่ม session ใหม่
2. ส่ง session_id เดิมทุก request ในการสนทนานั้น
3. Server จะ echo session_id กลับมาใน meta.session_id
4. ถ้าไม่ส่ง session_id server จะสร้าง UUID ใหม่ทุก request (ไม่มี history)

// Turn 1
{ "query": "บัตรประชาชนหมดอายุต้องทำยังไง", "mcp_endpoint_url": "http://185.84.161.145/mcp", "session_id": "550e8400-..." }

// Turn 2 — session_id เดิม
{ "query": "ต้องใช้เอกสารอะไรบ้าง", "mcp_endpoint_url": "http://185.84.161.145/mcp", "session_id": "550e8400-..." }

*พฤติกรรม:*
- History เก็บสูงสุด 10 turns (20 messages) ต่อ session
- Session หมดอายุหลัง 30 นาทีที่ไม่มีการใช้งาน

---

## Behavior ที่ควรรู้

### v1 /chat

| กรณี | data.answer | meta.synthesized | `da