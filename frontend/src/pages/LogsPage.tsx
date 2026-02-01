import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LogViewer } from '@/components/logs/LogViewer';
import { LogStream } from '@/components/logs/LogStream';

export function LogsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Logs</h1>
        <p className="text-muted-foreground">View and search application logs</p>
      </div>

      <Tabs defaultValue="viewer">
        <TabsList>
          <TabsTrigger value="viewer">Log Viewer</TabsTrigger>
          <TabsTrigger value="stream">Live Stream</TabsTrigger>
        </TabsList>

        <TabsContent value="viewer">
          <LogViewer />
        </TabsContent>

        <TabsContent value="stream">
          <LogStream />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default LogsPage;
