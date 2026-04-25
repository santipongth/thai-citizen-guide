import { supabase } from '@/integrations/supabase/client';

export interface ExecutiveKPIs {
  totalQuestions: number;
  momGrowth: number;
  yoyGrowth: number;
  uniqueCitizens: number;
  totalHoursSaved: number;
  costSaved: number;
  healthScore: number;
  uptime: number;
  satisfaction: number;
  avgResponseTime: number;
}

export interface AgencyScore {
  name: string;
  shortName: string;
  uptime: number;
  avgLatency: number;
  satisfaction: number;
  calls: number;
  grade: string;
}

export interface ExecutiveData {
  kpis: ExecutiveKPIs;
  agencyScorecard: AgencyScore[];
  monthlyTrend: { month: string; questions: number; satisfaction: number }[];
  topIssues: { topic: string; count: number; trend: string }[];
  weeklyBrief: string;
  generatedAt: string;
}

export async function fetchExecutiveSummary(): Promise<ExecutiveData> {
  const { data, error } = await supabase.functions.invoke('executive-summary');
  if (error) throw new Error(error.message);
  if (!data?.success) throw new Error(data?.error || 'Failed to load');
  return data.data as ExecutiveData;
}
