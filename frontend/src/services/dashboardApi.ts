import { api } from '@/lib/apiClient';
import type { DashboardStats } from '@/types';
import { dashboardStats as fallbackStats, agencyUsageData, weeklyTrendData, categoryData } from '@/data/mockData';

interface DashboardApiResponse {
  success: boolean;
  data: {
    stats: DashboardStats;
    agencyUsage: typeof agencyUsageData;
    weeklyTrend: typeof weeklyTrendData;
    categoryData: typeof categoryData;
  };
  responseTime: number;
}

async function fetchFromApi(): Promise<DashboardApiResponse> {
  return api.get<DashboardApiResponse>('/api/v1/dashboard/stats');
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  try {
    const res = await fetchFromApi();
    // Backend uses camelCase keys matching the original edge function output
    return res.data.stats;
  } catch {
    console.warn('Dashboard API failed, using fallback');
    return fallbackStats;
  }
}

export async function fetchAgencyUsage(): Promise<typeof agencyUsageData> {
  try {
    const res = await fetchFromApi();
    return res.data.agencyUsage;
  } catch {
    return [];
  }
}

export async function fetchWeeklyTrend(): Promise<typeof weeklyTrendData> {
  try {
    const res = await fetchFromApi();
    return res.data.weeklyTrend;
  } catch {
    return [];
  }
}

export async function fetchCategoryData(): Promise<typeof categoryData> {
  try {
    const res = await fetchFromApi();
    return res.data.categoryData;
  } catch {
    return [];
  }
}
