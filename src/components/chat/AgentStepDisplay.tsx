import { cn } from "@/lib/utils";
import type { AgentStep } from "@/data/mockData";

export function AgentStepDisplay({ steps, visibleCount }: { steps: AgentStep[]; visibleCount: number }) {
  return (
    <div className="bg-muted/50 rounded-lg p-3 mb-3 space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground mb-2">กระบวนการทำงานของ AI Agent:</p>
      {steps.slice(0, visibleCount).map((step, i) => {
        const isActive = i === visibleCount - 1 && visibleCount <= steps.length;
        const isDone = i < visibleCount - 1 || visibleCount > steps.length;
        return (
          <div key={i} className="flex items-center gap-2 text-xs animate-fade-in">
            <span>{step.icon}</span>
            <span className={cn(
              isDone && 'text-foreground',
              isActive && 'text-primary font-medium',
            )}>
              {step.label}
            </span>
            {isDone && <span className="text-green-600 text-[10px]">✓</span>}
            {isActive && <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />}
          </div>
        );
      })}
    </div>
  );
}
