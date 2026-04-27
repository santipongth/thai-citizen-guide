from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.executive_summary import ExecutiveData, ExecutiveKPIs

router = APIRouter(tags=["executive"])

@router.get("/executive-summary")
async def get_executive_summary() -> ExecutiveData:
    return ExecutiveData(
        kpis=ExecutiveKPIs(
            totalQuestions=0,
            momGrowth=0.0,
            yoyGrowth=0.0,
            uniqueCitizens=0,
            totalHoursSaved=0.0,
            costSaved=0.0,
            healthScore=0.0,
            uptime=0.0,
            satisfaction=0.0,
            avgResponseTime=0.0
        ),
        agencyScorecard=[],
        monthlyTrend=[],
        topIssues=[],
        weeklyBrief="",
        generatedAt=datetime.now(timezone.utc)
    )