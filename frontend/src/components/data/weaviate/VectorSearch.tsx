import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Search, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { weaviateApi, type VectorSearchResult } from '@/api/weaviate';

interface VectorSearchProps {
  collection: string;
}

export function VectorSearch({ collection }: VectorSearchProps) {
  const [query, setQuery] = useState('');
  const [limit, setLimit] = useState(10);
  const [results, setResults] = useState<VectorSearchResult[]>([]);

  const searchMutation = useMutation({
    mutationFn: () =>
      weaviateApi.search({
        collection,
        query,
        limit,
      }),
    onSuccess: (data) => {
      setResults(data);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    searchMutation.mutate();
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Vector Search</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="query">Search Query</Label>
              <Input
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query..."
              />
            </div>
            <div className="flex gap-4 items-end">
              <div className="space-y-2">
                <Label htmlFor="limit">Limit</Label>
                <Input
                  id="limit"
                  type="number"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                  className="w-24"
                  min={1}
                  max={100}
                />
              </div>
              <Button type="submit" disabled={!query || searchMutation.isPending}>
                {searchMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Search className="mr-2 h-4 w-4" />
                )}
                Search
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Results ({results.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.map((result) => (
                <div key={result.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <code className="text-sm text-muted-foreground">{result.id}</code>
                    <Badge variant="outline">
                      {(result.certainty * 100).toFixed(1)}% certainty
                    </Badge>
                  </div>
                  <pre className="text-sm bg-muted p-2 rounded overflow-auto max-h-32">
                    {JSON.stringify(result.properties, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
