import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/apiClient';

export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  agent_steps: any;
  sources: any;
  rating: string | null;
  created_at: string;
}

async function fetchConversationMessages(conversationId: string): Promise<ConversationMessage[]> {
  const data = await api.get<ConversationMessage[]>(
    `/api/v1/conversations/${conversationId}/messages`
  );
  return data ?? [];
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ['conversationMessages', conversationId],
    queryFn: () => fetchConversationMessages(conversationId!),
    enabled: !!conversationId,
    staleTime: 60 * 1000,
  });
}
