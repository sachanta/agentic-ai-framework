import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useLogSources } from '@/hooks/useLogs';
import type { LogFilters as LogFiltersType } from '@/api/logs';

interface LogFiltersProps {
  filters: LogFiltersType;
  onFiltersChange: (filters: LogFiltersType) => void;
}

export function LogFilters({ filters, onFiltersChange }: LogFiltersProps) {
  const { data: sources } = useLogSources();

  return (
    <div className="flex items-center gap-4">
      <div className="relative w-64">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search logs..."
          value={filters.search || ''}
          onChange={(e) => onFiltersChange({ ...filters, search: e.target.value || undefined })}
          className="pl-8"
        />
      </div>

      <Select
        value={filters.level?.[0] || 'all'}
        onValueChange={(value) =>
          onFiltersChange({
            ...filters,
            level: value === 'all' ? undefined : [value],
          })
        }
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="Level" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Levels</SelectItem>
          <SelectItem value="debug">Debug</SelectItem>
          <SelectItem value="info">Info</SelectItem>
          <SelectItem value="warning">Warning</SelectItem>
          <SelectItem value="error">Error</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.source || 'all'}
        onValueChange={(value) =>
          onFiltersChange({
            ...filters,
            source: value === 'all' ? undefined : value,
          })
        }
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Source" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Sources</SelectItem>
          {sources?.map((source) => (
            <SelectItem key={source} value={source}>
              {source}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
