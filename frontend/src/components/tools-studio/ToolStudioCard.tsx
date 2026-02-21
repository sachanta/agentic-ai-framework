import { Wrench, Hash, Server } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ToolStudioSummary } from '@/types/tool';

interface ToolStudioCardProps {
  tool: ToolStudioSummary;
  onSelect: (tool: ToolStudioSummary) => void;
}

export function ToolStudioCard({ tool, onSelect }: ToolStudioCardProps) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onSelect(tool)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg">{tool.display_name}</CardTitle>
            <div className="flex gap-1.5">
              <Badge variant="outline">{tool.category}</Badge>
              <Badge variant="secondary">{tool.platform_id}</Badge>
            </div>
          </div>
          <Wrench className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
          {tool.description}
        </p>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-1.5">
            <Hash className="h-3.5 w-3.5 text-muted-foreground" />
            <span>{tool.parameter_count} params</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Server className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="truncate text-xs font-mono">
              {tool.service_class}
            </span>
          </div>
          <div className="col-span-2 flex items-center gap-1.5">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                tool.status === 'available' ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            />
            <span className="text-xs text-muted-foreground capitalize">
              {tool.status}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
