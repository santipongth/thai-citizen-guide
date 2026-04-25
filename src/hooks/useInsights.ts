import { useQuery } from '@tanstack/react-query';
import { fetchAnalyticsInsights, fetchAgencyHealth, fetchUsageHeatmap, type HeatmapRange } from '@/services/insightsApi';

export function useAnalyticsInsights() {
  return useQuery({
    queryKey: ['analytics-insights'],
    queryFn: fetchAnalyticsInsights,
    staleTime: 5 * 60_000,
  });
}

export function useAgencyHealth() {
  return useQuery({
    queryKey: ['agency-health'],
    queryFn: fetchAgencyHealth,
    refetchInterval: 15_000,
    staleTime: 10_000,
  });
}

export function useUsageHeatmap(range: HeatmapRange = '7d') {
  return useQuery({
    queryKey: ['usage-heatmap', range],
    queryFn: () => fetchUsageHeatmap(range),
    staleTime: 60_000,
  });
}
