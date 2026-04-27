from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.insight import AnalyticsInsightsData, AgencyHealthData, BusiestInsight, HeatmapInsights, UsageHeatmapData, HeatmapRange

router = APIRouter(tags=["insight"])

@router.get("/analytics-insights")
async def get_insight_analytics_insights() -> AnalyticsInsightsData:
    return AnalyticsInsightsData(
        totalWeekQuestions=0,
        topicClusters=[],
        sentimentDist={"positive": 0, "neutral": 0, "negative": 0},
        noAnswerByAgency=[],
        dailyVolume=[],
        trendingTopics=[],
        decliningTopics=[],
        aiInsights="",
        recommendations=[],
        generatedAt=datetime.now(timezone.utc)
    )

@router.get("/agency-health")
async def get_insight_agency_health() -> AgencyHealthData:
    return AgencyHealthData(
        agencies=[],
        historical=[],
        incidents=[],
        slaCompliance=[],
        generatedAt=datetime.now(timezone.utc)
    )

@router.get("/usage-heatmap")
async def get_insight_usage_heatmap(range: HeatmapRange) -> UsageHeatmapData:
    return UsageHeatmapData(
        range=range,
        days=7,
        sampleSize=100,
        totalMessages=0,
        days_labels=[],
        hours=[],
        agencies=[],
        hourlyByAgency=[],
        dayHourMatrix=[],
        insights=HeatmapInsights(
            peakDay="",
            peakHour="",
            peakValue=0,
            totalRequests=0,
            businessHoursPercent=0.0,
            busiest=BusiestInsight(
                agency="",
                total=0,
                peakHour=0
            ),
            recommendation=""
        ),
        generatedAt=datetime.now(timezone.utc)
    )