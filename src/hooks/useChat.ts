import { useState, useRef, useEffect, useCallback } from 'react';
import type { ChatMessage, AgentStep } from '@/types';
import { sendChatQuery } from '@/services/chatApi';
import { saveConversation } from '@/services/historyApi';
import { updateMessageRating } from '@/services/feedbackApi';
import { mockAgentSteps, mockConversation } from '@/data/mockData';
import { generateUniqueId } from '@/lib/utils';
import { set } from 'date-fns';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [activeStepCount, setActiveStepCount] = useState(0);
  const [currentSteps, setCurrentSteps] = useState<AgentStep[]>(mockAgentSteps);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeStepCount]);

  const handleRate = useCallback((id: string, rating: 'up' | 'down', feedbackText?: string) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, rating } : m)));
    // Persist to database
    updateMessageRating(id, rating, feedbackText);
  }, []);

  const handleSend = useCallback(async (text?: string) => {
    const question = text || input.trim();
    if (!question || isTyping) return;

    const userMsg: ChatMessage = {
      id: generateUniqueId(),
      role: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    setActiveStepCount(0);

    // Animate placeholder steps while waiting
    // const placeholderSteps = mockAgentSteps;
    // setCurrentSteps(placeholderSteps);
    // placeholderSteps.forEach((_, i) => {
    //   setTimeout(() => setActiveStepCount(i + 1), (i + 1) * 500);
    // });

    try {
      const response = await sendChatQuery({ query: question, conversation_id: conversationId || undefined });

      if (response.success) {
        setConversationId(response.conversation_id);

        // Update steps with real data from API
        setCurrentSteps(response.data.agentSteps as AgentStep[]);
        setActiveStepCount(response.data.agentSteps.length);

        const aiMsgId = generateUniqueId();
        const aiMsg: ChatMessage = {
          id: aiMsgId,
          role: 'assistant',
          content: response.data.answer,
          timestamp: new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' }),
          agentSteps: response.data.agentSteps as AgentStep[],
          sources: response.data.references.map((ref) => ({
            agency: ref.agency,
            url: ref.url,
            title: ref.title,
          })),
          rating: null,
        };
        setMessages((prev) => [...prev, aiMsg]);
        setIsTyping(false);
        setActiveStepCount(0);

        // Save conversation to database
        // const autoTitle = question.length > 50 ? question.slice(0, 50) + '...' : question;
        // saveConversation({
        //   title: autoTitle,
        //   preview: question,
        //   agencies: response.data.agencies?.map((a) => a.name) || [],
        //   status: 'success',
        //   responseTime: `${(response.responseTime / 1000).toFixed(1)} วินาที`,
        //   messages: [
        //     { id: userMsg.id, role: 'user', content: question },
        //     {
        //       id: aiMsgId,
        //       role: 'assistant',
        //       content: response.data.answer,
        //       agentSteps: response.data.agentSteps,
        //       sources: response.data.references,
        //     },
        //   ],
        // });

        return;
      }
    } catch {
      // console.warn('API call failed, falling back to mock data');
      setCurrentSteps([]);
      setActiveStepCount(0);
      setIsTyping(false);
      setMessages((prev) => [...prev, {
        id: generateUniqueId(),
        role: 'assistant',
        content: 'ขออภัย ฉันไม่สามารถตอบคำถามได้ในขณะนี้ โปรดลองอีกครั้งในภายหลัง',
        timestamp: new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' }),
        rating: null,
      }]);
    }

    // Fallback to mock data
    // setTimeout(() => {
    //   const aiMsg: ChatMessage = {
    //     ...mockConversation[1],
    //     id: generateUniqueId(),
    //     timestamp: new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' }),
    //     rating: null,
    //   };
    //   setMessages((prev) => [...prev, aiMsg]);
    //   setIsTyping(false);
    //   setActiveStepCount(0);
    // }, (placeholderSteps.length + 1) * 500);
  }, [input, isTyping]);

  const reset = useCallback(() => {
    setMessages([]);
    setIsTyping(false);
    setActiveStepCount(0);
    setInput('');
    setCurrentSteps(mockAgentSteps);
    setConversationId(null);
  }, []);

  return {
    messages,
    input,
    setInput,
    isTyping,
    activeStepCount,
    currentSteps,
    scrollRef,
    handleSend,
    handleRate,
    reset,
    hasMessages: messages.length > 0,
  };
}
