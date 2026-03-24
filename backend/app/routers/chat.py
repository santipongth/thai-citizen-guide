"""
AI Chat router — LangGraph multi-agent router with OpenAI LLM.

Graph
-----
  START → route (tool-calling agent: load_agencies tool + routing decision)
        → query_agency (parallel fan-out via Send) → synthesize → END

Each selected agency is queried in parallel using LangGraph Send; results
are merged back into the main state via operator.add reducers.

Agency source:  REST GET /api/v1/agencies  (settings.API_BASE_URL).
LLM:            OpenAI-compatible endpoint configured in settings.

Endpoint
--------
  POST  /api/v1/chat
"""

import json
import operator
import time
from typing import Annotated, Any

import httpx
from fastapi import APIRouter
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.types import Send
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from app.config import settings
from app.llm import get_llm, load_agencies as load_agencies_tool

router = APIRouter(prefix="/chat", tags=["Chat"])


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    query: str


# ---------------------------------------------------------------------------
# LangGraph state types
# ---------------------------------------------------------------------------

class AgencyResult(TypedDict):
    agency_id: str
    agency_name: str
    agency_short_name: str
    answer: str
    references: list[dict]
    confidence: float
    success: bool
    error: str | None


class AgentStep(TypedDict):
    icon: str
    label: str
    status: str   # "done" | "error"


class ChatState(TypedDict):
    query: str
    agencies: list[dict]                                         # from agencies://list
    target_ids: list[str]                                        # router's decision
    agency_results: Annotated[list[AgencyResult], operator.add]  # fan-in (parallel)
    agent_steps: Annotated[list[AgentStep], operator.add]        # fan-in (parallel)
    answer: str
    references: list[dict]
    confidence: float


# Per-agency mini-state (used as Send payload)
class AgencyQueryState(TypedDict):
    query: str
    agency: dict


# ---------------------------------------------------------------------------
# Node: route  (tool-calling agent — loads agencies then decides routing)
# ---------------------------------------------------------------------------

async def route(state: ChatState) -> dict:
    """
    LLM agent that:
      1. Calls load_agencies tool to fetch active agencies.
      2. Decides which agency IDs are relevant to the query.
    Returns agencies + target_ids in one step.
    """
    query = state["query"]
    llm_with_tools = get_llm(temperature=0).bind_tools([load_agencies_tool])

    messages = [
        SystemMessage(content=(
            "You are a router for a Thai government AI chatbot. "
            "First, call the load_agencies tool to discover available agencies. "
            "After receiving the list, return ONLY a JSON object: "
            "{\"agency_ids\": [\"<uuid>\", ...]} with 1–3 IDs that are CLEARLY "
            "relevant to the user's question. "
            "If the question is general or no agency clearly matches, "
            "return {\"agency_ids\": []}."
        )),
        HumanMessage(content=f"Route this query: {query}"),
    ]

    # ── Step 1: LLM calls load_agencies tool ────────────────────────────────
    agencies: list[dict] = []
    response = await llm_with_tools.ainvoke(messages)

    if response.tool_calls:
        messages.append(response)
        for tc in response.tool_calls:
            raw = await load_agencies_tool.ainvoke(tc.get("args") or {})
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            agencies = parsed if isinstance(parsed, list) else parsed.get("agencies", [])
            messages.append(ToolMessage(content=json.dumps(agencies, ensure_ascii=False), tool_call_id=tc["id"]))

        # ── Step 2: LLM routes based on the loaded agencies ─────────────────
        routing_response = await get_llm(temperature=0).ainvoke(messages)
        content = routing_response.content.strip()
    else:
        # LLM skipped the tool — treat its reply as the routing answer
        content = response.content.strip()

    # ── Parse agency_ids ────────────────────────────────────────────────────
    target_ids: list[str] = []
    try:
        if "```" in content:
            parts = content.split("```")
            content = parts[1][4:] if parts[1].startswith("json") else parts[1]
        target_ids = json.loads(content.strip()).get("agency_ids", [])[:3]
    except Exception as exc:
        print(f"[chat:route] Could not parse routing response: {exc}")

    known_ids = {str(a["id"]) for a in agencies}
    target_ids = [aid for aid in target_ids if aid in known_ids]

    if target_ids:
        selected_names = [a["name"] for a in agencies if str(a["id"]) in target_ids]
        step_label = f"เลือกหน่วยงาน: {', '.join(selected_names)}"
    else:
        step_label = "ไม่พบหน่วยงานที่ตรงกัน — ตอบด้วย AI ทั่วไป"

    return {
        "agencies":    agencies,
        "target_ids":  target_ids,
        "agent_steps": [
            {"icon": "🔍", "label": "กำลังวิเคราะห์คำถาม...",  "status": "done"},
            {"icon": "📋", "label": step_label,                 "status": "done"},
        ],
    }


# ---------------------------------------------------------------------------
# Fan-out edge: route → Send(query_agency) × N
# ---------------------------------------------------------------------------

def fan_out(state: ChatState) -> list[Send] | str:
    """Emit one Send per selected agency. Falls through to synthesize if none."""
    agencies_by_id = {str(a["id"]): a for a in state["agencies"]}
    sends = [
        Send("query_agency", {"query": state["query"], "agency": agencies_by_id[aid]})
        for aid in state["target_ids"]
        if aid in agencies_by_id
    ]
    return sends if sends else "synthesize"


# ---------------------------------------------------------------------------
# Real endpoint caller (REST / MCP / A2A best-effort)
# ---------------------------------------------------------------------------

async def _call_real_endpoint(
    agency: dict,
    query: str,
) -> tuple[str | None, list[dict], float]:
    """
    Try to call the agency's configured API endpoint with `query`.
    Returns (answer_text, references, confidence) or (None, [], 0) on failure.
    """
    endpoint_url: str = agency.get("endpoint_url") or ""
    api_endpoints: list[dict] = agency.get("api_endpoints") or []

    if not endpoint_url or not api_endpoints:
        return None, [], 0.0

    # Pick the first endpoint that has a path
    ep = next((e for e in api_endpoints if e.get("path")), None)
    if not ep:
        return None, [], 0.0

    method = (ep.get("method") or "GET").upper()
    url = endpoint_url.rstrip("/") + "/" + ep["path"].lstrip("/")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method == "GET":
                resp = await client.get(url, params={"q": query, "query": query})
            else:
                resp = await client.post(url, json={"query": query})

        if resp.status_code == 200:
            try:
                data = resp.json()
                return json.dumps(data, ensure_ascii=False, indent=2)[:4000], [], 0.85
            except Exception:
                return resp.text[:2000], [], 0.65
    except Exception as exc:
        print(f"[chat:endpoint] {agency.get('name')}: {exc}")

    return None, [], 0.0


# ---------------------------------------------------------------------------
# Node: query_agency  (called in parallel via Send)
# ---------------------------------------------------------------------------

async def query_agency(state: AgencyQueryState) -> dict:
    """
    Query a single agency — real endpoint first, LLM fallback.
    Returns dict with keys `agency_results` and `agent_steps` (both lists,
    merged into ChatState via operator.add).
    """
    agency: dict = state["agency"]
    query: str  = state["query"]

    agency_name  = agency.get("name", "")
    agency_short = agency.get("short_name", "")
    agency_id    = str(agency.get("id", ""))

    steps: list[AgentStep] = [{
        "icon":   "🔗",
        "label":  f"กำลังสืบค้นจาก {agency_short or agency_name}...",
        "status": "done",
    }]

    # ── Attempt real endpoint ───────────────────────────────────────────────
    answer, references, confidence = await _call_real_endpoint(agency, query)

    # ── LLM fallback ────────────────────────────────────────────────────────
    if answer is None:
        try:
            data_scope = ", ".join(agency.get("data_scope") or []) or "ข้อมูลทั่วไป"
            system_prompt = (
                f"คุณคือผู้เชี่ยวชาญด้านข้อมูลของ {agency_name} ({agency_short}).\n"
                f"ขอบเขตข้อมูลที่รับผิดชอบ: {data_scope}.\n\n"
                "ตอบคำถามเป็นภาษาไทย ให้ข้อมูลที่ถูกต้องและเป็นประโยชน์ "
                "อ้างอิงกฎหมาย/ระเบียบที่เกี่ยวข้องถ้ามี "
                "และระบุหากไม่มีข้อมูลเพียงพอ"
            )
            resp = await get_llm(temperature=0.2).ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": query},
            ])
            answer = resp.content
            confidence = 0.75
            steps.append({
                "icon":   "🤖",
                "label":  f"AI สร้างคำตอบแทน {agency_short or agency_name}",
                "status": "done",
            })
        except Exception as exc:
            print(f"[chat:query_agency] LLM fallback for {agency_name}: {exc}")
            answer = f"ไม่สามารถดึงข้อมูลจาก {agency_name} ได้ในขณะนี้"
            confidence = 0.0

    result: AgencyResult = {
        "agency_id":         agency_id,
        "agency_name":       agency_name,
        "agency_short_name": agency_short,
        "answer":            answer or "",
        "references":        references,
        "confidence":        confidence,
        "success":           bool(answer),
        "error":             None if answer else "No data available",
    }

    return {
        "agency_results": [result],
        "agent_steps":    steps,
    }


# ---------------------------------------------------------------------------
# Node: synthesize
# ---------------------------------------------------------------------------

async def synthesize(state: ChatState) -> dict:
    """Combine all agency answers into one coherent Thai response via LLM."""
    query          = state["query"]
    agency_results = state.get("agency_results") or []

    if not agency_results:
        # No agency was selected → answer directly with a general-purpose LLM call
        general_answer = "ขออภัย ไม่สามารถตอบคำถามได้ในขณะนี้"
        try:
            resp = await get_llm(temperature=0.5).ainvoke([
                {
                    "role": "system",
                    "content": (
                        "คุณคือผู้ช่วย AI ที่ให้ข้อมูลทั่วไปเป็นภาษาไทย "
                        "ตอบคำถามอย่างชัดเจน กระชับ และเป็นประโยชน์ "
                        "ใช้ Markdown formatting ให้อ่านง่าย"
                    ),
                },
                {"role": "user", "content": query},
            ])
            general_answer = resp.content
        except Exception as exc:
            print(f"[chat:synthesize] General LLM error: {exc}")
        return {
            "answer":      general_answer,
            "references":  [],
            "confidence":  0.6,
            "agent_steps": [
                {"icon": "🤖", "label": "AI ตอบคำถามทั่วไป (ไม่ผ่านหน่วยงาน)", "status": "done"},
            ],
        }

    all_references = [
        {"agency": r["agency_name"], **ref}
        for r in agency_results
        for ref in r.get("references") or []
    ]
    avg_confidence = sum(r["confidence"] for r in agency_results) / len(agency_results)

    agency_context = "\n\n".join(
        f"### ข้อมูลจาก {r['agency_name']} ({r['agency_short_name']})\n{r['answer']}"
        for r in agency_results
        if r.get("success") and r.get("answer")
    )

    if not agency_context:
        # All agencies failed — just concatenate raw answers
        return {
            "answer":      "\n\n---\n\n".join(r["answer"] for r in agency_results),
            "references":  all_references,
            "confidence":  avg_confidence,
            "agent_steps": [{"icon": "📝", "label": "รวบรวมข้อมูล (ไม่มีการสังเคราะห์)", "status": "done"}],
        }

    # ── LLM synthesis ───────────────────────────────────────────────────────
    system_prompt = (
        "คุณคือ AI ผู้ช่วยภาครัฐไทย ทำหน้าที่สังเคราะห์ข้อมูลจากหลายหน่วยงานราชการ\n\n"
        "กฎ:\n"
        "- ตอบเป็นภาษาไทยเสมอ\n"
        "- ใช้ Markdown formatting (หัวข้อ, bullet, ตัวหนา) ให้อ่านง่าย\n"
        "- อ้างอิงชื่อหน่วยงานที่เป็นแหล่งข้อมูลในคำตอบ\n"
        "- เชื่อมโยงข้อมูลจากหลายหน่วยงานให้สอดคล้องและไม่ซ้ำซ้อน\n"
        "- ห้ามเพิ่มข้อมูลที่ไม่มีในแหล่งที่ให้มา\n"
        "- จบด้วยข้อแนะนำเพิ่มเติมหากเหมาะสม"
    )
    user_prompt = (
        f'คำถามจากประชาชน: "{query}"\n\n'
        f"ข้อมูลจากหน่วยงานราชการ:\n\n{agency_context}\n\n"
        "กรุณาสังเคราะห์เป็นคำตอบที่ครบถ้วนและเข้าใจง่ายสำหรับประชาชน"
    )

    final_answer = agency_context  # fallback
    try:
        resp = await get_llm(temperature=0.3).ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ])
        final_answer = resp.content
    except Exception as exc:
        print(f"[chat:synthesize] LLM error: {exc}")

    return {
        "answer":      final_answer,
        "references":  all_references,
        "confidence":  avg_confidence,
        "agent_steps": [
            {"icon": "🤖", "label": "AI สังเคราะห์คำตอบจากทุกหน่วยงาน", "status": "done"},
            {"icon": "📝", "label": "สังเคราะห์คำตอบเสร็จสิ้น",         "status": "done"},
        ],
    }


# ---------------------------------------------------------------------------
# Build & compile the LangGraph
# ---------------------------------------------------------------------------

def _build_graph() -> Any:
    g = StateGraph(ChatState)

    g.add_node("route",        route)          # tool-calling agent (load + route)
    g.add_node("query_agency", query_agency)
    g.add_node("synthesize",   synthesize)

    g.add_edge(START, "route")

    # fan_out returns list[Send] for parallel agency queries,
    # or "synthesize" directly when no agencies matched
    g.add_conditional_edges("route", fan_out, ["query_agency", "synthesize"])

    g.add_edge("query_agency", "synthesize")
    g.add_edge("synthesize",   END)

    return g.compile()


_graph = _build_graph()


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

@router.post("", summary="Send a query and get a synthesised AI response")
async def chat(body: ChatRequest) -> dict:
    start = time.time()
    query = body.query.strip()

    if not query:
        return {"success": False, "error": "Missing query"}

    try:
        state: ChatState = await _graph.ainvoke({
            "query":          query,
            "agencies":       [],
            "target_ids":     [],
            "agency_results": [],
            "agent_steps":    [],
            "answer":         "",
            "references":     [],
            "confidence":     0.0,
        })
    except Exception as exc:
        print(f"[chat] Graph error: {exc}")
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(exc)}

    return {
        "success": True,
        "data": {
            "answer":     state.get("answer", ""),
            "references": state.get("references", []),
            "agentSteps": state.get("agent_steps", []),
            "agencies": [
                {
                    "id":        r["agency_id"],
                    "name":      r["agency_name"],
                    "shortName": r["agency_short_name"],
                }
                for r in state.get("agency_results", [])
            ],
            "confidence": state.get("confidence", 0.0),
        },
        "responseTime": int((time.time() - start) * 1000),
    }
