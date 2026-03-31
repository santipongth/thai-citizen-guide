import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/apiClient';
import { ConnectionLog } from '@/types/connectionLog';

export interface ConnectionLogResponse {
  search: string | null;
  page: number;
  page_size: number;
  items: ConnectionLog[];
  total_items: number;
}

export interface ConnectionLogParams {
  page?: number;
  limit?: number;
  search?: string;
}

async function fetchConnectionLogs(params: ConnectionLogParams = {}): Promise<ConnectionLogResponse> {
  const qs = new URLSearchParams();
  if (params.page) qs.set('page', String(params.page));
  if (params.limit) qs.set('limit', String(params.limit));
  if (params.search) qs.set('search', params.search);
  const query = qs.toString();
  return await api.get<ConnectionLogResponse>(`/api/v1/connection-logs${query ? `?${query}` : ''}`);
}

export function useConnectionLogs(params: ConnectionLogParams = {}) {
  return useQuery({
    queryKey: ['connection-logs', params],
    queryFn: () => fetchConnectionLogs(params),
    staleTime: 15_000,
    refetchInterval: 30_000,
    placeholderData: (prev) => prev,
  });
}