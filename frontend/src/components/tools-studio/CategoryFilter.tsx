import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import type { ToolStudioCategory } from '@/types/tool';

interface CategoryFilterProps {
  categories: ToolStudioCategory[];
  selected: string | undefined;
  onSelect: (category: string | undefined) => void;
  totalToolCount: number;
}

export function CategoryFilter({
  categories,
  selected,
  onSelect,
  totalToolCount,
}: CategoryFilterProps) {
  return (
    <Tabs
      value={selected ?? 'all'}
      onValueChange={(v) => onSelect(v === 'all' ? undefined : v)}
    >
      <TabsList>
        <TabsTrigger value="all">
          All
          <Badge variant="secondary" className="ml-2">
            {totalToolCount}
          </Badge>
        </TabsTrigger>
        {categories.map((cat) => (
          <TabsTrigger key={cat.name} value={cat.name}>
            {cat.name.charAt(0).toUpperCase() + cat.name.slice(1)}
            <Badge variant="secondary" className="ml-2">
              {cat.count}
            </Badge>
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
