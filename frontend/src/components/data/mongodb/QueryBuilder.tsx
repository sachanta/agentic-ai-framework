import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Play, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { mongodbApi, type MongoDocument } from '@/api/mongodb';
import { formatNumber } from '@/utils/format';

interface QueryBuilderProps {
  collection: string;
}

export function QueryBuilder({ collection }: QueryBuilderProps) {
  const [filter, setFilter] = useState('{}');
  const [results, setResults] = useState<MongoDocument[]>([]);
  const [total, setTotal] = useState(0);

  const queryMutation = useMutation({
    mutationFn: () => {
      let parsedFilter = {};
      try {
        parsedFilter = JSON.parse(filter);
      } catch {
        // Invalid JSON, use empty filter
      }
      return mongodbApi.query(collection, { filter: parsedFilter, limit: 100 });
    },
    onSuccess: (data) => {
      setResults(data.documents);
      setTotal(data.total);
    },
  });

  const handleQuery = () => {
    queryMutation.mutate();
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Query Builder</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Filter (JSON)</Label>
            <Textarea
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder='{"field": "value"}'
              className="font-mono"
              rows={4}
            />
            <p className="text-xs text-muted-foreground">
              Enter a MongoDB query filter. Example: {"{"}"status": "active"{"}"} or {"{"}"age": {"{"}"$gt": 18{"}"}{"}"}
            </p>
          </div>
          <Button onClick={handleQuery} disabled={queryMutation.isPending}>
            {queryMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Execute Query
          </Button>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Results</CardTitle>
            <Badge variant="outline">{formatNumber(total)} total</Badge>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[400px] overflow-auto">
              {results.map((doc) => (
                <div key={doc._id} className="p-3 border rounded">
                  <div className="flex items-center justify-between mb-2">
                    <code className="text-sm text-muted-foreground">{doc._id}</code>
                  </div>
                  <pre className="text-sm bg-muted p-2 rounded overflow-auto max-h-32">
                    {JSON.stringify(doc, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {queryMutation.isSuccess && results.length === 0 && (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">No documents match the query</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
