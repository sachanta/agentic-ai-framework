/**
 * useToast hook
 *
 * Compatible API for toast notifications using the notification store
 */
import { useNotificationStore, type NotificationType } from '@/store/notificationStore';

interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
  duration?: number;
}

interface ToastReturn {
  id: string;
  dismiss: () => void;
}

export function useToast() {
  const { addNotification, removeNotification, notifications } = useNotificationStore();

  const toast = (options: ToastOptions): ToastReturn => {
    // Map variant to notification type
    let type: NotificationType = 'info';
    if (options.variant === 'destructive') {
      type = 'error';
    }

    // Use a counter for ID
    const id = String(Date.now());

    addNotification({
      type,
      title: options.title,
      message: options.description,
      duration: options.duration,
    });

    return {
      id,
      dismiss: () => removeNotification(id),
    };
  };

  return {
    toast,
    toasts: notifications,
    dismiss: removeNotification,
  };
}

export { useToast as default };
