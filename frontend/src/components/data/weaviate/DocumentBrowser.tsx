import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Trash2, Eye, RefreshCw, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { weaviateApi } from '@/api/weaviate';
import { notify } from '@/store/notificationStore';
import { formatDate } from '@/utils/format';

interface DocumentBrowserProps {
  collectionName: string;
}

export function DocumentBrowser({ collectionName }: DocumentBrowserProps) {
  const [page, setPage] = useState(1);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Record<string, unknown> | null>(null);
  const [newDocProperties, setNewDocProperties] = useState('{}');
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['weaviate', 'documents', collectionName, page],
    queryFn: () => weaviateApi.listDocuments(collectionName, page, 20),
    enabled: !!collectionName,
  });

  const addMutation = useMutation({
    mutationFn: (properties: Record<string, unknown>) =>
      weaviateApi.addDocument(collectionName, properties),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'documents', collectionName] });
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'collections'] });
      notify.success('Document added');
      setIsAddOpen(false);
      setNewDocProperties('{}');
    },
    onError: (error: Error) => {
      notify.error('Failed to add document', error.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => weaviateApi.deleteDocument(collectionName, docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'documents', collectionName] });
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'collections'] });
      notify.success('Document deleted');
    },
    onError: (error: Error) => {
      notify.error('Failed to delete document', error.message);
    },
  });

  const handleAddDocument = () => {
    try {
      const properties = JSON.parse(newDocProperties);
      addMutation.mutate(properties);
    } catch {
      notify.error('Invalid JSON', 'Please enter valid JSON for document properties');
    }
  };

  const handleDelete = (docId: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(docId);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Documents in {collectionName}</CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Document
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Document</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Properties (JSON)</Label>
                  <Textarea
                    value={newDocProperties}
                    onChange={(e) => setNewDocProperties(e.target.value)}
                    rows={10}
                    className="font-mono text-sm"
                    placeholder='{"title": "Document Title", "content": "Document content..."}'
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsAddOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddDocument} disabled={addMutation.isPending}>
                    Add Document
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : data?.items?.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">No documents found</p>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Properties</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((doc: { id: string; properties: Record<string, unknown>; createdAt: string }) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-mono text-sm">{doc.id}</TableCell>
                    <TableCell className="max-w-md truncate">
                      {JSON.stringify(doc.properties).slice(0, 100)}...
                    </TableCell>
                    <TableCell>{formatDate(doc.createdAt)}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setSelectedDoc(doc.properties)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl">
                            <DialogHeader>
                              <DialogTitle>Document Details</DialogTitle>
                            </DialogHeader>
                            <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-sm">
                              {JSON.stringify(selectedDoc, null, 2)}
                            </pre>
                          </DialogContent>
                        </Dialog>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(doc.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {data && data.total_pages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  Page {page} of {data.total_pages} ({data.total} documents)
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                    disabled={page === data.total_pages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
