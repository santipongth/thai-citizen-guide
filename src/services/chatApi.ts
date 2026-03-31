import { api } from '@/lib/apiClient';
import type { AgentStep } from '@/types';

export interface ChatApiRequest {
  query: string;
  conversation_id?: string;
}

export interface ChatApiResponse {
  success: boolean;
  data: {
    message_id: string;
    answer: string;
    references: { agency: string; title: string; url: string }[];
    agentSteps: AgentStep[];
    agencies: { id: string; name: string; icon: string }[];
    confidence: number;
  };
  conversation_id: string;
  responseTime: number;
}

export async function sendChatQuery(request: ChatApiRequest): Promise<ChatApiResponse> {
  return api.post<ChatApiResponse>('/api/v1/chat', request);
}
