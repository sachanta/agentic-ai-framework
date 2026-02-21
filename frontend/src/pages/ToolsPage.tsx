import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Wrench } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { useToolsStudioList, useToolsStudioCategories } from '@/hooks/useToolsStudio';
import { CategoryFilter } from '@/components/tools-studio/CategoryFilter';
import { ToolStudioCard } from '@/components/tools-studio/ToolStudioCard';
import type { ToolStudioSummary } from '@/types/tool';

export function ToolsPage() {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(
    undefined,
  );

  const { data, isLoading } = useToolsStudioList(selectedCategory);
  const { data: categories } = useToolsStudioCategories();

  const tools = data?.tools ?? [];

  const handleSelectTool = (tool: ToolStudioSummary) => {
    // Encode tool_id: replace / with -- for URL safety
    const encodedId = tool.tool_id.replace(/\//g, '--');
    navigate(`/tools/${encodedId}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Wrench className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Tools Studio</h1>
          <p className="text-muted-foreground">
            Discover and test all framework tools across every service
          </p>
        </div>
      </div>

      <CategoryFilter
        categories={categories ?? []}
        selected={selectedCategory}
        onSelect={setSelectedCategory}
        totalToolCount={data?.total ?? 0}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[200px] rounded-lg" />
          ))}
        </div>
      ) : tools.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No tools discovered.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tools.map((tool) => (
            <ToolStudioCard
              key={tool.tool_id}
              tool={tool}
              onSelect={handleSelectTool}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default ToolsPage;
