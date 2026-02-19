/**
 * Visual workflow progress tracker
 *
 * Displays the HITL workflow steps with status indicators:
 * ●────────●────────◉────────○────────○
 * Research  Review   Write    Final    Done
 * ✓         ✓        ⏳       ...      ...
 */
import { cn } from '@/lib/utils';
import { Check, Circle, Loader2 } from 'lucide-react';
import type { WorkflowStepStatus } from '@/types/newsletter';

export interface WorkflowStep {
  id: string;
  label: string;
  description?: string;
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  { id: 'research', label: 'Research', description: 'Discover relevant articles' },
  { id: 'research_review', label: 'Review Articles', description: 'Select and reorder articles' },
  { id: 'writing', label: 'Generate', description: 'Create newsletter content' },
  { id: 'content_review', label: 'Review Content', description: 'Edit and approve content' },
  { id: 'subject_review', label: 'Select Subject', description: 'Choose a subject line' },
  { id: 'final_review', label: 'Final Review', description: 'Confirm and schedule' },
];

interface WorkflowTrackerProps {
  currentStep: string | null;
  completedSteps: string[];
  status: WorkflowStepStatus | null;
  className?: string;
}

export function WorkflowTracker({
  currentStep,
  completedSteps,
  status,
  className,
}: WorkflowTrackerProps) {
  const currentStepIndex = WORKFLOW_STEPS.findIndex((s) => s.id === currentStep);

  const getStepStatus = (stepId: string): 'completed' | 'current' | 'pending' | 'error' => {
    // When workflow is completed, all steps are done
    if (status === 'completed') return 'completed';
    if (completedSteps.includes(stepId)) return 'completed';
    // All steps before the current step are implicitly completed
    const stepIndex = WORKFLOW_STEPS.findIndex((s) => s.id === stepId);
    if (currentStepIndex >= 0 && stepIndex >= 0 && stepIndex < currentStepIndex) return 'completed';
    if (currentStep === stepId) {
      if (status === 'failed') return 'error';
      return 'current';
    }
    return 'pending';
  };

  return (
    <div className={cn('w-full', className)}>
      {/* Progress bar */}
      <div className="relative flex items-center justify-between">
        {/* Background line */}
        <div className="absolute left-0 right-0 top-1/2 h-0.5 -translate-y-1/2 bg-muted" />

        {/* Progress line */}
        <div
          className="absolute left-0 top-1/2 h-0.5 -translate-y-1/2 bg-primary transition-all duration-500"
          style={{
            width: `${status === 'completed' ? 100 : Math.max(0, (currentStepIndex / (WORKFLOW_STEPS.length - 1)) * 100)}%`,
          }}
        />

        {/* Step indicators */}
        {WORKFLOW_STEPS.map((step) => {
          const stepStatus = getStepStatus(step.id);

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center">
              {/* Step circle */}
              <div
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all',
                  stepStatus === 'completed' && 'border-primary bg-primary text-primary-foreground',
                  stepStatus === 'current' && 'border-primary bg-background',
                  stepStatus === 'pending' && 'border-muted bg-background',
                  stepStatus === 'error' && 'border-destructive bg-destructive text-destructive-foreground'
                )}
              >
                {stepStatus === 'completed' && <Check className="h-4 w-4" />}
                {stepStatus === 'current' && (
                  <Loader2 className="h-4 w-4 text-primary animate-spin" />
                )}
                {stepStatus === 'pending' && (
                  <Circle className="h-3 w-3 text-muted-foreground" />
                )}
                {stepStatus === 'error' && <span className="text-xs font-bold">!</span>}
              </div>

              {/* Step label */}
              <span
                className={cn(
                  'mt-2 text-xs font-medium text-center max-w-[80px]',
                  stepStatus === 'completed' && 'text-primary',
                  stepStatus === 'current' && 'text-primary',
                  stepStatus === 'pending' && 'text-muted-foreground',
                  stepStatus === 'error' && 'text-destructive'
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Current step description */}
      {currentStep && (
        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            {WORKFLOW_STEPS.find((s) => s.id === currentStep)?.description}
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for sidebar/header
 */
interface WorkflowTrackerCompactProps {
  currentStep: string | null;
  completedSteps: string[];
  status: WorkflowStepStatus | null;
}

export function WorkflowTrackerCompact({
  currentStep,
  completedSteps,
  status,
}: WorkflowTrackerCompactProps) {
  const currentStepData = WORKFLOW_STEPS.find((s) => s.id === currentStep);
  const completedCount = completedSteps.length;
  const totalSteps = WORKFLOW_STEPS.length;

  return (
    <div className="flex items-center gap-3">
      {/* Progress indicator */}
      <div className="flex items-center gap-1">
        {WORKFLOW_STEPS.map((step) => {
          const isCompleted = status === 'completed' || completedSteps.includes(step.id);
          const isCurrent = status !== 'completed' && step.id === currentStep;

          return (
            <div
              key={step.id}
              className={cn(
                'h-2 w-2 rounded-full transition-all',
                isCompleted && 'bg-primary',
                isCurrent && 'bg-primary animate-pulse',
                !isCompleted && !isCurrent && 'bg-muted'
              )}
            />
          );
        })}
      </div>

      {/* Status text */}
      <span className="text-sm text-muted-foreground">
        {status === 'awaiting_approval' ? (
          <span className="text-amber-600 dark:text-amber-400">
            Awaiting approval: {currentStepData?.label}
          </span>
        ) : status === 'running' ? (
          <span>
            Step {completedCount + 1}/{totalSteps}: {currentStepData?.label}
          </span>
        ) : status === 'completed' ? (
          <span className="text-green-600 dark:text-green-400">Completed</span>
        ) : status === 'failed' ? (
          <span className="text-destructive">Failed</span>
        ) : status === 'cancelled' ? (
          <span className="text-muted-foreground">Cancelled</span>
        ) : (
          <span>Not started</span>
        )}
      </span>
    </div>
  );
}

export default WorkflowTracker;
