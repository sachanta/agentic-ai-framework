import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { CollectionForm } from './CollectionForm';
import { weaviateApi } from '@/api/weaviate';
import { notify } from '@/store/notificationStore';
import { formatNumber } from '@/utils/format';

interface CollectionListProps {
  onSelectCollection: (name: string) => void;
}

export function CollectionList({ onSelectCollection }: CollectionListProps) {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: collections, isLoading, refetch } = useQuery({
    queryKey: ['weaviate', 'collections'],
    queryFn: () => weaviateApi.listCollections(),
  });

  const deleteMutation = useMutation({
    mutationFn: weaviateApi.deleteCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'collections'] });
      notify.success('Collection deleted');
    },
    onError: (error: Error) => {
      notify.error('Failed to delete collection', error.message);
    },
  });

  const handleDelete = (name: string) => {
    if (confirm(`Are you sure you want to delete collection "${name}"?`)) {
      deleteMutation.mutate(name);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Collections</CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                New Collection
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Collection</DialogTitle>
              </DialogHeader>
              <CollectionForm onSuccess={() => setIsCreateOpen(false)} />
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : collections?.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">No collections found</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Vectorizer</TableHead>
                <TableHead>Properties</TableHead>
                <TableHead>Objects</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {collections?.map((collection) => (
                <TableRow
                  key={collection.name}
                  className="cursor-pointer"
                  onClick={() => onSelectCollection(collection.name)}
                >
                  <TableCell className="font-medium">{collection.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{collection.vectorizer}</Badge>
                  </TableCell>
                  <TableCell>{collection.properties.length}</TableCell>
                  <TableCell>{formatNumber(collection.object_count)}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(collection.name);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
