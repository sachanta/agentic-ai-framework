import { SettingsForm } from '@/components/settings/SettingsForm';
import { PendingUsersPanel } from '@/components/admin/PendingUsersPanel';

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure application settings</p>
      </div>
      <PendingUsersPanel />
      <SettingsForm />
    </div>
  );
}

export default SettingsPage;
