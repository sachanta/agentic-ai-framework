/**
 * Approval action buttons for checkpoints
 *
 * Provides Approve, Edit, and Reject buttons with loading states
 */
import { Button } from '@/components/ui/button';
import { Check, Pencil, RotateCcw, Loader2 } from 'lucide-react';
import type { CheckpointAction } from '@/types/newsletter';

interface ApprovalActionsProps {
  onApprove: () => void;
  onEdit?: () => void;
  onReject: () => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
  disabled?: boolean;
  showEdit?: boolean;
  approveLabel?: string;
  rejectLabel?: string;
  className?: string;
}

export function ApprovalActions({
  onApprove,
  onEdit,
  onReject,
  isLoading = false,
  loadingAction = null,
  disabled = false,
  showEdit = true,
  approveLabel = 'Approve',
  rejectLabel = 'Re-generate',
  className,
}: ApprovalActionsProps) {
  const isApproving = isLoading && loadingAction === 'approve';
  const isEditing = isLoading && loadingAction === 'edit';
  const isRejecting = isLoading && loadingAction === 'reject';

  return (
    <div className={className}>
      <div className="flex items-center justify-center gap-3">
        {/* Approve Button */}
        <Button
          onClick={onApprove}
          disabled={disabled || isLoading}
          className="min-w-[120px]"
        >
          {isApproving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Check className="h-4 w-4 mr-2" />
          )}
          {approveLabel}
        </Button>

        {/* Edit Button */}
        {showEdit && onEdit && (
          <Button
            variant="outline"
            onClick={onEdit}
            disabled={disabled || isLoading}
            className="min-w-[120px]"
          >
            {isEditing ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Pencil className="h-4 w-4 mr-2" />
            )}
            Edit
          </Button>
        )}

        {/* Reject Button */}
        <Button
          variant="outline"
          onClick={onReject}
          disabled={disabled || isLoading}
          className="min-w-[120px] text-destructive hover:text-destructive"
        >
          {isRejecting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RotateCcw className="h-4 w-4 mr-2" />
          )}
          {rejectLabel}
        </Button>
      </div>
    </div>
  );
}

/**
 * Compact version for inline use
 */
interface ApprovalActionsCompactProps {
  onApprove: () => void;
  onReject: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function ApprovalActionsCompact({
  onApprove,
  onReject,
  isLoading = false,
  disabled = false,
}: ApprovalActionsCompactProps) {
  return (
    <div className="flex items-center gap-2">
      <Button
        size="sm"
        onClick={onApprove}
        disabled={disabled || isLoading}
      >
        {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={onReject}
        disabled={disabled || isLoading}
        className="text-destructive hover:text-destructive"
      >
        <RotateCcw className="h-3 w-3" />
      </Button>
    </div>
  );
}

export default ApprovalActions;
