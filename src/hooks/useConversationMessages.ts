import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';

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
  const { data, error } = await supabase
    .from('messages')
    .select('*')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true });

  if (error) throw error;
  return (data || []) as ConversationMessage[];
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ['conversationMessages', conversationId],
    queryFn: () => fetchConversationMessages(conversationId!),
    enabled: !!conversationId,
    staleTime: 60 * 1000,
  });
}
