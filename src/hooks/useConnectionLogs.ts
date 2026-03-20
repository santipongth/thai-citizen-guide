import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/apiClient';

export interface ConnectionLog {
  id: string;
  agencyId: string;
  action: string;
  connectionType: string;
  status: string;
  latencyMs: number;
  detail: string;
  createdAt: string;
}

async function fetchConnectionLogs(agencyId: string): Promise<ConnectionLog[]> {
  try {
    const data = await api.get<Array<{
      id: string;
      agency_id: string;
      action: string;
      connection_type: string;
      status: string;
      latency_ms: number;
      detail: string;
      created_at: string;
    }>>(`/api/v1/agencies/${agencyId}/connection-logs`);

    return (data ?? []).map((row) => ({
      id: row.id,
      agencyId: row.agency_id,
      action: row.action,
      connectionType: row.connection_type,
      status: row.status,
      latencyMs: row.latency_ms,
      detail: row.detail,
      createdAt: row.created_at,
    }));
  } catch (err: any) {
    console.warn('Failed to fetch connection logs', err?.message);
    return [];
  }
}

export function useConnectionLogs(agencyId: string | undefined) {
  return useQuery({
    queryKey: ['connection-logs', agencyId],
    queryFn: () => fetchConnectionLogs(agencyId!),
    enabled: !!agencyId,
    staleTime: 15_000,
  });
}
