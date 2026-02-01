import { SettingsForm } from '@/components/settings/SettingsForm';

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure application settings</p>
      </div>
      <SettingsForm />
    </div>
  );
}

export default SettingsPage;
