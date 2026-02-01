import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Database, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { mongodbApi } from '@/api/mongodb';
import { formatNumber, formatBytes } from '@/utils/format';
import { cn } from '@/lib/utils';

interface CollectionBrowserProps {
  onSelectCollection: (database: string, collection: string) => void;
}

export function CollectionBrowser({ onSelectCollection }: CollectionBrowserProps) {
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  const { data: collections, isLoading, refetch } = useQuery({
    queryKey: ['mongodb', 'collections'],
    queryFn: () => mongodbApi.listCollections(),
  });

  const handleSelect = (collectionName: string) => {
    setSelectedCollection(collectionName);
    onSelectCollection('default', collectionName);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Collections
        </CardTitle>
        <Button variant="ghost" size="icon" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : collections?.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">No collections found</p>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-1">
              {collections?.map((collection) => (
                <button
                  key={collection.name}
                  className={cn(
                    'flex items-center justify-between w-full p-3 rounded text-left text-sm transition-colors',
                    selectedCollection === collection.name
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                  onClick={() => handleSelect(collection.name)}
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-medium">{collection.name}</span>
                    <span className={cn(
                      'text-xs',
                      selectedCollection === collection.name
                        ? 'text-primary-foreground/70'
                        : 'text-muted-foreground'
                    )}>
                      {formatBytes(collection.avgDocumentSize)} avg size
                    </span>
                  </div>
                  <Badge
                    variant={selectedCollection === collection.name ? 'secondary' : 'outline'}
                    className="text-xs"
                  >
                    {formatNumber(collection.documentCount)} docs
                  </Badge>
                </button>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
