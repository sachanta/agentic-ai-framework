import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from '@/components/ui/toast';
import { useNotificationStore } from '@/store/notificationStore';

export function Toaster() {
  const { notifications, removeNotification } = useNotificationStore();

  const getVariant = (type: string) => {
    switch (type) {
      case 'success':
        return 'success';
      case 'error':
        return 'destructive';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <ToastProvider>
      {notifications.map((notification) => (
        <Toast
          key={notification.id}
          variant={getVariant(notification.type)}
          onOpenChange={(open) => {
            if (!open) removeNotification(notification.id);
          }}
        >
          <div className="grid gap-1">
            <ToastTitle>{notification.title}</ToastTitle>
            {notification.message && (
              <ToastDescription>{notification.message}</ToastDescription>
            )}
          </div>
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  );
}
