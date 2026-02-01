import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Trash2, Edit, RefreshCw, Plus, Save, X } from 'lucide-react';
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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { mongodbApi } from '@/api/mongodb';
import { notify } from '@/store/notificationStore';

interface DocumentViewerProps {
  collectionName: string;
}

export function DocumentViewer({ collectionName }: DocumentViewerProps) {
  const [page, setPage] = useState(1);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingDoc, setEditingDoc] = useState<{ id: string; content: string } | null>(null);
  const [newDocContent, setNewDocContent] = useState('{}');
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['mongodb', 'documents', collectionName, page],
    queryFn: () => mongodbApi.listDocuments(collectionName, page, 20),
    enabled: !!collectionName,
  });

  const createMutation = useMutation({
    mutationFn: (document: Record<string, unknown>) =>
      mongodbApi.createDocument(collectionName, document),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'documents', collectionName] });
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'collections'] });
      notify.success('Document created');
      setIsAddOpen(false);
      setNewDocContent('{}');
    },
    onError: (error: Error) => {
      notify.error('Failed to create document', error.message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, document }: { id: string; document: Record<string, unknown> }) =>
      mongodbApi.updateDocument(collectionName, id, document),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'documents', collectionName] });
      notify.success('Document updated');
      setEditingDoc(null);
    },
    onError: (error: Error) => {
      notify.error('Failed to update document', error.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => mongodbApi.deleteDocument(collectionName, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'documents', collectionName] });
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'collections'] });
      notify.success('Document deleted');
    },
    onError: (error: Error) => {
      notify.error('Failed to delete document', error.message);
    },
  });

  const handleCreate = () => {
    try {
      const document = JSON.parse(newDocContent);
      createMutation.mutate(document);
    } catch {
      notify.error('Invalid JSON', 'Please enter valid JSON');
    }
  };

  const handleUpdate = () => {
    if (!editingDoc) return;
    try {
      const document = JSON.parse(editingDoc.content);
      updateMutation.mutate({ id: editingDoc.id, document });
    } catch {
      notify.error('Invalid JSON', 'Please enter valid JSON');
    }
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(id);
    }
  };

  const startEditing = (doc: { _id: string; [key: string]: unknown }) => {
    setEditingDoc({
      id: doc._id,
      content: JSON.stringify(doc, null, 2),
    });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Documents</CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                New Document
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Document</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Document (JSON)</Label>
                  <Textarea
                    value={newDocContent}
                    onChange={(e) => setNewDocContent(e.target.value)}
                    rows={12}
                    className="font-mono text-sm"
                    placeholder='{"field": "value"}'
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsAddOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreate} disabled={createMutation.isPending}>
                    Create
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {editingDoc && (
          <div className="mb-4 p-4 border rounded-lg bg-muted/50">
            <div className="flex justify-between items-center mb-2">
              <Label>Editing Document: {editingDoc.id}</Label>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditingDoc(null)}
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleUpdate}
                  disabled={updateMutation.isPending}
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save
                </Button>
              </div>
            </div>
            <Textarea
              value={editingDoc.content}
              onChange={(e) =>
                setEditingDoc({ ...editingDoc, content: e.target.value })
              }
              rows={10}
              className="font-mono text-sm"
            />
          </div>
        )}

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
                  <TableHead>_id</TableHead>
                  <TableHead>Preview</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((doc: { _id: string; [key: string]: unknown }) => (
                  <TableRow key={doc._id}>
                    <TableCell className="font-mono text-sm">{doc._id}</TableCell>
                    <TableCell className="max-w-md">
                      <pre className="text-xs bg-muted p-2 rounded truncate overflow-hidden">
                        {JSON.stringify(doc, null, 0).slice(0, 150)}...
                      </pre>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => startEditing(doc)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(doc._id)}
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
