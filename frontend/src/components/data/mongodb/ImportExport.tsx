import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Download, FileJson, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { mongodbApi } from '@/api/mongodb';
import { notify } from '@/store/notificationStore';

interface ImportExportProps {
  collectionName: string;
}

interface ImportResult {
  imported: number;
  failed: number;
  total: number;
}

export function ImportExport({ collectionName }: ImportExportProps) {
  const [jsonInput, setJsonInput] = useState('');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const importMutation = useMutation({
    mutationFn: (documents: Array<Record<string, unknown>>) =>
      mongodbApi.importDocuments(collectionName, documents),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'documents', collectionName] });
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'collections'] });
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
      importMutation.mutate(documents);
    } catch {
      notify.error('Invalid JSON', 'Please enter valid JSON array of documents');
    }
  };

  const handleExport = async () => {
    try {
      const data = await mongodbApi.exportDocuments(collectionName, exportFormat);

      const blob = new Blob(
        [exportFormat === 'json' ? JSON.stringify(data, null, 2) : data],
        { type: exportFormat === 'json' ? 'application/json' : 'text/csv' }
      );

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${collectionName}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      notify.success('Export completed', `Downloaded ${collectionName}.${exportFormat}`);
    } catch (error) {
      notify.error('Export failed', (error as Error).message);
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
        <CardTitle>Import / Export</CardTitle>
        <CardDescription>
          Bulk data operations for {collectionName}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="import">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="import">Import</TabsTrigger>
            <TabsTrigger value="export">Export</TabsTrigger>
          </TabsList>

          <TabsContent value="import" className="space-y-4">
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
                rows={10}
                className="font-mono text-sm"
                placeholder={`[
  {"name": "Document 1", "value": 100},
  {"name": "Document 2", "value": 200}
]`}
              />
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
          </TabsContent>

          <TabsContent value="export" className="space-y-4">
            <div className="space-y-2">
              <Label>Export Format</Label>
              <Select
                value={exportFormat}
                onValueChange={(value) => setExportFormat(value as 'json' | 'csv')}
              >
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {exportFormat === 'json'
                  ? 'Export as JSON array with full document structure'
                  : 'Export as CSV with flattened fields (nested objects as JSON strings)'}
              </p>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm">
                This will export all documents from the <strong>{collectionName}</strong> collection.
              </p>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleExport}>
                <Download className="mr-2 h-4 w-4" />
                Export Collection
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
