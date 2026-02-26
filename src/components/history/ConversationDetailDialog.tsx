import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Loader2, User, Bot } from 'lucide-react';
import { useConversationMessages } from '@/hooks/useConversationMessages';
import type { HistoryItem } from '@/services/historyApi';
import ReactMarkdown from 'react-markdown';

interface ConversationDetailDialogProps {
  conversation: HistoryItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ConversationDetailDialog({ conversation, open, onOpenChange }: ConversationDetailDialogProps) {
  const { data: messages = [], isLoading } = useConversationMessages(
    open ? conversation?.id ?? null : null
  );

  if (!conversation) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold">{conversation.title}</DialogTitle>
          <div className="flex items-center gap-2 flex-wrap pt-1">
            {conversation.agencies.map((a, i) => (
              <Badge key={i} variant="outline" className="text-[10px]">{a}</Badge>
            ))}
            {conversation.responseTime && (
              <span className="text-[10px] text-muted-foreground">⏱ {conversation.responseTime}</span>
            )}
            <span className="text-[10px] text-muted-foreground">{conversation.date}</span>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          )}

          {!isLoading && messages.length === 0 && (
            <p className="text-center text-sm text-muted-foreground py-8">
              ไม่มีข้อความในสนทนานี้
            </p>
          )}

          {!isLoading && messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={`rounded-lg px-3 py-2 max-w-[80%] text-sm ${
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none [&>p]:my-1 [&>ul]:my-1">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="shrink-0 w-7 h-7 rounded-full bg-primary flex items-center justify-center">
                  <User className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
