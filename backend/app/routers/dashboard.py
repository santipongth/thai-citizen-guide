"""
Dashboard stats route — port of the Supabase `dashboard-stats` edge function.

Endpoint
--------
  GET  /dashboard/stats
"""

import random
import time

from fastapi import APIRouter, Depends
from app.auth.dependencies import require_admin, get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", summary="Get dashboard statistics and charts data")
async def dashboard_stats(user: User = Depends(get_current_user)) -> dict:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="ไม่สามารถเข้าถึงข้อมูลนี้ได้")
    
    start = time.time()

    stats = {
        "totalQuestions": 48290 + random.randint(0, 50),
        "todayQuestions": 150 + random.randint(0, 20),
        "avgResponseTime": f"{(2.0 + random.random() * 0.6):.1f} วินาที",
        "satisfactionRate": round(93.5 + random.random() * 2, 1),
    }

    agency_usage = [
        {"name": "อย.", "value": 12450 + random.randint(0, 100), "fill": "hsl(145 55% 40%)"},
        {"name": "กรมสรรพากร", "value": 18320 + random.randint(0, 100), "fill": "hsl(213 70% 45%)"},
        {"name": "กรมการปกครอง", "value": 9870 + random.randint(0, 100), "fill": "hsl(25 85% 55%)"},
        {"name": "กรมที่ดิน", "value": 7650 + random.randint(0, 100), "fill": "hsl(280 50% 50%)"},
    ]

    weekly_trend = [
        {"day": "จันทร์", "questions": 170 + random.randint(0, 30)},
        {"day": "อังคาร", "questions": 200 + random.randint(0, 30)},
        {"day": "พุธ", "questions": 185 + random.randint(0, 30)},
        {"day": "พฤหัสบดี", "questions": 230 + random.randint(0, 30)},
        {"day": "ศุกร์", "questions": 210 + random.randint(0, 30)},
        {"day": "เสาร์", "questions": 80 + random.randint(0, 30)},
        {"day": "อาทิตย์", "questions": 55 + random.randint(0, 30)},
    ]

    category_data = [
        {"category": "สอบถามข้อมูล", "count": 22450 + random.randint(0, 200)},
        {"category": "ตรวจสอบสถานะ", "count": 12300 + random.randint(0, 200)},
        {"category": "ขั้นตอนดำเนินการ", "count": 8900 + random.randint(0, 200)},
        {"category": "กฎหมาย/ระเบียบ", "count": 4640 + random.randint(0, 200)},
    ]

    return {
        "success": True,
        "data": {
            "stats": stats,
            "agencyUsage": agency_usage,
            "weeklyTrend": weekly_trend,
            "categoryData": category_data,
        },
        "responseTime": int((time.time() - start) * 1000),
    }
