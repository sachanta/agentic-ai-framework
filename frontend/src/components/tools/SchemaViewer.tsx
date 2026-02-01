import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { ToolSchema } from '@/types/tool';

interface SchemaViewerProps {
  schema: ToolSchema;
}

export function SchemaViewer({ schema }: SchemaViewerProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Function Schema</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Name</p>
              <p className="font-mono">{schema.name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Description</p>
              <p>{schema.description}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Parameters</CardTitle>
        </CardHeader>
        <CardContent>
          {schema.parameters.length === 0 ? (
            <p className="text-sm text-muted-foreground">No parameters</p>
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
                {schema.parameters.map((param) => (
                  <TableRow key={param.name}>
                    <TableCell className="font-mono">{param.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{param.type}</Badge>
                    </TableCell>
                    <TableCell>
                      {param.required ? (
                        <Badge variant="destructive">Yes</Badge>
                      ) : (
                        <Badge variant="secondary">No</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {param.default !== undefined ? (
                        <code className="text-sm">{JSON.stringify(param.default)}</code>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{param.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {schema.returns && (
        <Card>
          <CardHeader>
            <CardTitle>Return Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <p className="text-sm text-muted-foreground">Type:</p>
                <Badge variant="outline">{schema.returns.type}</Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Description:</p>
                <p>{schema.returns.description}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>JSON Schema</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="p-4 bg-muted rounded-md overflow-auto text-sm">
            {JSON.stringify(schema, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
