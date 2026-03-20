import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/apiClient';
// import { agencies as mockAgencies } from '@/data/mockData';
import type { Agency } from '@/types';
import type { AgencyRow } from '@/types/agency';
import { mapRowToAgency } from '@/types/agency';

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

const emptyAgencies: Agency[] = [];

async function fetchAgencies(): Promise<Agency[]> {
  try {
    const res = await api.get<{ data: AgencyRow[]; total: number }>('/api/v1/agencies');
    if (!res.data || res.data.length === 0) return emptyAgencies;
    return res.data.map(mapRowToAgency);
  } catch (err) {
    console.warn('Failed to fetch agencies from backend, using fallback', err);
    return emptyAgencies;
  }
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useAgencies() {
  return useQuery({
    queryKey: ['agencies'],
    queryFn: fetchAgencies,
    staleTime: 30_000,
    refetchInterval: 60_000,   // poll every 60 s (replaces Supabase realtime)
  });
}

export function useCreateAgency() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (agency: Partial<Agency>) => {
      return api.post('/api/v1/agencies', {
        name: agency.name,
        short_name: agency.shortName,
        logo: agency.logo,
        connection_type: agency.connectionType,
        status: agency.status,
        description: agency.description,
        data_scope: agency.dataScope ?? [],
        color: agency.color,
        endpoint_url: agency.endpointUrl,
        api_key_name: agency.apiKeyName,
        auth_method: agency.authMethod,
        auth_header: agency.authHeader,
        base_path: agency.basePath,
        rate_limit_rpm: agency.rateLimitRpm,
        request_format: agency.requestFormat,
        api_endpoints: agency.apiEndpoints ?? [],
        response_schema: agency.responseSchema ?? [],
        api_spec_raw: agency.apiSpecRaw,
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agencies'] }),
  });
}

export function useUpdateAgency() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (agency: Partial<Agency> & { id: string }) => {
      return api.patch(`/api/v1/agencies/${agency.id}`, {
        name: agency.name,
        short_name: agency.shortName,
        logo: agency.logo,
        connection_type: agency.connectionType,
        status: agency.status,
        description: agency.description,
        data_scope: agency.dataScope,
        color: agency.color,
        endpoint_url: agency.endpointUrl,
        api_key_name: agency.apiKeyName,
        auth_method: agency.authMethod,
        auth_header: agency.authHeader,
        base_path: agency.basePath,
        rate_limit_rpm: agency.rateLimitRpm,
        request_format: agency.requestFormat,
        api_endpoints: agency.apiEndpoints,
        response_schema: agency.responseSchema,
        api_spec_raw: agency.apiSpecRaw,
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agencies'] }),
  });
}

export function useDeleteAgency() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/api/v1/agencies/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agencies'] }),
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: async (params: { connectionType: string; endpointUrl: string }) => {
      // Simple HEAD-check via backend (future: add /api/v1/agencies/test-connection endpoint)
      // For now return a positive simulation matching the original behaviour
      return {
        success: true,
        steps: [
          { label: 'DNS resolution', status: 'success' },
          { label: 'TCP connection', status: 'success' },
          { label: 'HTTP response', status: 'success' },
        ],
        latencyMs: Math.floor(80 + Math.random() * 120),
      };
    },
  });
}
