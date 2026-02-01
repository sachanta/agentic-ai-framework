import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, FileJson, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { weaviateApi } from '@/api/weaviate';
import { notify } from '@/store/notificationStore';

interface BulkImportProps {
  collectionName: string;
}

interface ImportResult {
  imported: number;
  failed: number;
  total: number;
}

export function BulkImport({ collectionName }: BulkImportProps) {
  const [jsonInput, setJsonInput] = useState('');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const importMutation = useMutation({
    mutationFn: (documents: Array<{ properties: Record<string, unknown> }>) =>
      weaviateApi.bulkImport(collectionName, documents),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'documents', collectionName] });
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'collections'] });
      setImportResult(result);
      if (result.failed === 0) {
        notify.success('Import completed', `Successfully imported ${result.imported} documents`);
      } else {
        notify.warning('Import completed with errors', `${result.imported} imported, ${result.failed} failed`);
      }
    },
    onError: (error: Error) => {
      notify.error('Import failed', error.message);
    },
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setJsonInput(content);
    };
    reader.readAsText(file);
  };

  const handleImport = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      const documents = Array.isArray(parsed) ? parsed : [parsed];

      const formattedDocs = documents.map((doc) => ({
        properties: doc.properties || doc,
      }));

      importMutation.mutate(formattedDocs);
    } catch {
      notify.error('Invalid JSON', 'Please enter valid JSON array of documents');
    }
  };

  const handleClear = () => {
    setJsonInput('');
    setImportResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bulk Import</CardTitle>
        <CardDescription>
          Import multiple documents into {collectionName}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Upload JSON File</Label>
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="mr-2 h-4 w-4" />
              Choose File
            </Button>
            <Button variant="outline" onClick={handleClear}>
              Clear
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Or paste JSON directly</Label>
          <Textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            rows={12}
            className="font-mono text-sm"
            placeholder={`[
  {"title": "Document 1", "content": "Content 1..."},
  {"title": "Document 2", "content": "Content 2..."}
]`}
          />
          <p className="text-xs text-muted-foreground">
            JSON array of documents. Each document should contain the properties for the collection.
          </p>
        </div>

        {importMutation.isPending && (
          <div className="space-y-2">
            <Label>Importing...</Label>
            <Progress value={50} className="animate-pulse" />
          </div>
        )}

        {importResult && (
          <div className={`p-4 rounded-lg ${importResult.failed > 0 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'}`}>
            <div className="flex items-center gap-2 mb-2">
              {importResult.failed > 0 ? (
                <AlertCircle className="h-5 w-5 text-yellow-600" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
              <span className="font-medium">
                {importResult.failed > 0 ? 'Import completed with errors' : 'Import successful'}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Total:</span>{' '}
                <span className="font-medium">{importResult.total}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Imported:</span>{' '}
                <span className="font-medium text-green-600">{importResult.imported}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Failed:</span>{' '}
                <span className="font-medium text-red-600">{importResult.failed}</span>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <Button
            onClick={handleImport}
            disabled={!jsonInput.trim() || importMutation.isPending}
          >
            <FileJson className="mr-2 h-4 w-4" />
            Import Documents
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
