import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';
import { useToolsStudioDetail, useTryTool } from '@/hooks/useToolsStudio';

export function ToolInspectorPage() {
  const { toolId: rawToolId } = useParams<{ toolId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Decode tool_id: replace -- back to /
  const toolId = rawToolId?.replace(/--/g, '/') ?? '';

  const { data: detail, isLoading } = useToolsStudioDetail(toolId);
  const tryMutation = useTryTool();

  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [tryOutput, setTryOutput] = useState<unknown>(null);
  const [tryError, setTryError] = useState<string | null>(null);

  const handleParamChange = (name: string, value: string) => {
    setParamValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleTry = () => {
    if (!detail) return;

    // Parse parameter values to their expected types
    const parsed: Record<string, unknown> = {};
    for (const param of detail.parameters) {
      const raw = paramValues[param.name];
      if (raw === undefined || raw === '') {
        if (param.required) {
          toast({
            variant: 'destructive',
            title: 'Missing parameter',
            description: `"${param.name}" is required`,
          });
          return;
        }
        continue;
      }
      if (param.type === 'integer') {
        parsed[param.name] = parseInt(raw, 10);
      } else if (param.type === 'number') {
        parsed[param.name] = parseFloat(raw);
      } else if (param.type === 'boolean') {
        parsed[param.name] = raw === 'true';
      } else if (param.type === 'array' || param.type === 'object') {
        try {
          parsed[param.name] = JSON.parse(raw);
        } catch {
          toast({
            variant: 'destructive',
            title: 'Invalid JSON',
            description: `"${param.name}" must be valid JSON`,
          });
          return;
        }
      } else {
        parsed[param.name] = raw;
      }
    }

    setTryOutput(null);
    setTryError(null);

    tryMutation.mutate(
      { toolId, data: { parameters: parsed } },
      {
        onSuccess: (res) => {
          if (res.success) {
            setTryOutput(res.output);
            toast({
              title: 'Success',
              description: `Executed in ${res.duration_ms}ms`,
            });
          } else {
            setTryError(res.error ?? 'Unknown error');
            toast({
              variant: 'destructive',
              title: 'Execution failed',
              description: res.error,
            });
          }
        },
        onError: (err) => {
          const msg = err instanceof Error ? err.message : 'Request failed';
          setTryError(msg);
          toast({
            variant: 'destructive',
            title: 'Request error',
            description: msg,
          });
        },
      },
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/tools')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Tools Studio
        </Button>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Tool not found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/tools')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{detail.display_name}</h1>
          <div className="flex gap-2 mt-1">
            <Badge variant="outline">{detail.category}</Badge>
            <Badge variant="secondary">{detail.platform_id}</Badge>
            <Badge variant="secondary">{detail.service_class}</Badge>
          </div>
        </div>
      </div>

      {detail.description && (
        <p className="text-muted-foreground">{detail.description}</p>
      )}

      <Tabs defaultValue="schema">
        <TabsList>
          <TabsTrigger value="schema">Schema</TabsTrigger>
          <TabsTrigger value="try">Try It</TabsTrigger>
          <TabsTrigger value="info">Info</TabsTrigger>
        </TabsList>

        <TabsContent value="schema" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Parameters</CardTitle>
            </CardHeader>
            <CardContent>
              {detail.parameters.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No parameters required.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Required</TableHead>
                      <TableHead>Default</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detail.parameters.map((p) => (
                      <TableRow key={p.name}>
                        <TableCell className="font-mono text-sm">
                          {p.name}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{p.type}</Badge>
                        </TableCell>
                        <TableCell>{p.required ? 'Yes' : 'No'}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {p.default != null ? String(p.default) : '-'}
                        </TableCell>
                        <TableCell className="text-sm">
                          {p.description}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {detail.returns && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Returns</CardTitle>
              </CardHeader>
              <CardContent>
                <code className="text-sm bg-muted px-2 py-1 rounded">
                  {detail.returns}
                </code>
              </CardContent>
            </Card>
          )}

          {detail.requires.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Requirements</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  {detail.requires.map((req) => (
                    <Badge key={req} variant="destructive">
                      {req}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="try" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Parameters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {detail.parameters.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No parameters needed. Click Execute to run.
                </p>
              ) : (
                detail.parameters.map((p) => (
                  <div key={p.name} className="space-y-1.5">
                    <Label htmlFor={p.name}>
                      {p.name}
                      {p.required && (
                        <span className="text-destructive ml-1">*</span>
                      )}
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({p.type})
                      </span>
                    </Label>
                    <Input
                      id={p.name}
                      placeholder={
                        p.default != null
                          ? `Default: ${String(p.default)}`
                          : p.description
                      }
                      value={paramValues[p.name] ?? ''}
                      onChange={(e) =>
                        handleParamChange(p.name, e.target.value)
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      {p.description}
                    </p>
                  </div>
                ))
              )}

              <Button
                onClick={handleTry}
                disabled={tryMutation.isPending}
                className="w-full"
              >
                {tryMutation.isPending ? 'Executing...' : 'Execute'}
              </Button>
            </CardContent>
          </Card>

          {(tryOutput != null || tryError) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  {tryError ? 'Error' : 'Output'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted rounded p-4 overflow-auto max-h-96 text-sm">
                  {tryError
                    ? tryError
                    : JSON.stringify(tryOutput, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="info" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tool Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Tool ID</span>
                  <p className="font-mono">{detail.tool_id}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Name</span>
                  <p className="font-mono">{detail.name}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Category</span>
                  <p>{detail.category}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Platform</span>
                  <p>{detail.platform_id}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Service Class</span>
                  <p className="font-mono">{detail.service_class}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status</span>
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${
                        detail.status === 'available'
                          ? 'bg-green-500'
                          : 'bg-yellow-500'
                      }`}
                    />
                    <span className="capitalize">{detail.status}</span>
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Parameters</span>
                  <p>{detail.parameter_count}</p>
                </div>
                {detail.returns && (
                  <div>
                    <span className="text-muted-foreground">Return Type</span>
                    <p className="font-mono">{detail.returns}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default ToolInspectorPage;
