import { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, X, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { weaviateApi, PDFUploadProgress, PDFUploadResponse } from '@/api/weaviate';
import { notify } from '@/store/notificationStore';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

type UploadStage = 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';

interface UploadState {
  stage: UploadStage;
  progress: number;
  message: string;
  currentChunk?: number;
  totalChunks?: number;
  chunksStored?: number;
  error?: string;
  result?: {
    chunksCreated: number;
    chunksStored: number;
    chunksFailed: number;
    totalPages: number;
    processingTime: number;
  };
}

const STAGE_LABELS: Record<string, string> = {
  validating: 'Validating',
  extracting: 'Extracting Text',
  chunking: 'Chunking',
  embedding: 'Generating Embeddings',
  storing: 'Storing to Database',
  completed: 'Completed',
  failed: 'Failed',
  heartbeat: 'Processing',
};

export function PDFUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>({
    stage: 'idle',
    progress: 0,
    message: '',
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const validateFile = (file: File): string | null => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF files are supported';
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB`;
    }
    return null;
  };

  const handleFileSelect = useCallback((selectedFile: File) => {
    const error = validateFile(selectedFile);
    if (error) {
      notify.error('Invalid file', error);
      return;
    }

    setFile(selectedFile);
    // Auto-populate title from filename
    if (!title) {
      const nameWithoutExt = selectedFile.name.replace(/\.pdf$/i, '');
      setTitle(nameWithoutExt);
    }
  }, [title]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, [handleFileSelect]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const connectToProgress = (uploadId: string) => {
    const eventSource = weaviateApi.createPDFProgressEventSource(uploadId);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const progress: PDFUploadProgress = JSON.parse(event.data);

        if (progress.stage === 'completed') {
          setUploadState({
            stage: 'completed',
            progress: 100,
            message: progress.message,
            result: {
              chunksCreated: progress.total_chunks || 0,
              chunksStored: progress.chunks_stored || 0,
              chunksFailed: (progress.total_chunks || 0) - (progress.chunks_stored || 0),
              totalPages: 0, // Will be updated from final result
              processingTime: 0,
            },
          });
          eventSource.close();
          notify.success('Upload completed', progress.message);
        } else if (progress.stage === 'failed') {
          setUploadState({
            stage: 'failed',
            progress: 0,
            message: progress.message,
            error: progress.error,
          });
          eventSource.close();
          notify.error('Upload failed', progress.error || progress.message);
        } else if (progress.stage !== 'heartbeat') {
          setUploadState({
            stage: 'processing',
            progress: progress.progress,
            message: progress.message,
            currentChunk: progress.current_chunk,
            totalChunks: progress.total_chunks,
            chunksStored: progress.chunks_stored,
          });
        }
      } catch (err) {
        console.error('Failed to parse progress event:', err);
      }
    };

    eventSource.onerror = () => {
      if (uploadState.stage === 'processing') {
        setUploadState((prev) => ({
          ...prev,
          stage: 'failed',
          error: 'Connection lost. Check upload status manually.',
        }));
        notify.error('Connection lost', 'Progress updates stopped');
      }
      eventSource.close();
    };
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploadState({
      stage: 'uploading',
      progress: 0,
      message: 'Starting upload...',
    });

    try {
      const response: PDFUploadResponse = await weaviateApi.uploadPDF(file, {
        title: title || file.name.replace(/\.pdf$/i, ''),
      });

      setUploadId(response.upload_id);
      setUploadState({
        stage: 'processing',
        progress: 5,
        message: 'Processing PDF...',
      });

      // Connect to SSE for progress updates
      connectToProgress(response.upload_id);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadState({
        stage: 'failed',
        progress: 0,
        message: 'Upload failed',
        error: errorMessage,
      });
      notify.error('Upload failed', errorMessage);
    }
  };

  const handleCancel = async () => {
    if (!uploadId) return;

    try {
      await weaviateApi.cancelPDFUpload(uploadId);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      setUploadState({
        stage: 'idle',
        progress: 0,
        message: 'Upload cancelled',
      });
      notify.info('Upload cancelled', 'The upload has been cancelled');
    } catch (error) {
      console.error('Failed to cancel upload:', error);
    }
  };

  const handleReset = () => {
    setFile(null);
    setTitle('');
    setUploadId(null);
    setUploadState({
      stage: 'idle',
      progress: 0,
      message: '',
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };

  const isProcessing = uploadState.stage === 'uploading' || uploadState.stage === 'processing';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload PDF</CardTitle>
        <CardDescription>
          Upload a PDF document for RAG processing. The document will be extracted, chunked, and stored with embeddings.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Drop Zone */}
        {uploadState.stage === 'idle' && (
          <>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                ${isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileInputChange}
                className="hidden"
              />
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-1">
                {file ? file.name : 'Drop a PDF file here'}
              </p>
              <p className="text-sm text-muted-foreground">
                {file
                  ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
                  : 'or click to browse (max 50MB)'}
              </p>
            </div>

            {file && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="title">Document Title</Label>
                  <Input
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter document title"
                  />
                  <p className="text-xs text-muted-foreground">
                    This title will be used to identify the document in search results
                  </p>
                </div>

                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={handleReset}>
                    Clear
                  </Button>
                  <Button onClick={handleUpload}>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload PDF
                  </Button>
                </div>
              </>
            )}
          </>
        )}

        {/* Processing State */}
        {isProcessing && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <FileText className="h-10 w-10 text-primary" />
              <div className="flex-1">
                <p className="font-medium">{file?.name}</p>
                <p className="text-sm text-muted-foreground">
                  {STAGE_LABELS[uploadState.message.toLowerCase().split(' ')[0]] || uploadState.message}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={handleCancel}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{uploadState.message}</span>
                <span>{Math.round(uploadState.progress)}%</span>
              </div>
              <Progress value={uploadState.progress} />
            </div>

            {uploadState.totalChunks && (
              <p className="text-sm text-muted-foreground text-center">
                Processing chunk {uploadState.currentChunk || 0} of {uploadState.totalChunks}
                {uploadState.chunksStored !== undefined && ` (${uploadState.chunksStored} stored)`}
              </p>
            )}

            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">This may take a few moments for large documents</span>
            </div>
          </div>
        )}

        {/* Completed State */}
        {uploadState.stage === 'completed' && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-green-50 border border-green-200">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="font-medium text-green-800">Upload Successful</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Chunks Created:</span>{' '}
                  <span className="font-medium">{uploadState.result?.chunksCreated || 0}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Chunks Stored:</span>{' '}
                  <span className="font-medium text-green-600">{uploadState.result?.chunksStored || 0}</span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                {uploadState.message}
              </p>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleReset}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Another
              </Button>
            </div>
          </div>
        )}

        {/* Failed State */}
        {uploadState.stage === 'failed' && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-red-50 border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <span className="font-medium text-red-800">Upload Failed</span>
              </div>
              <p className="text-sm text-red-700">
                {uploadState.error || uploadState.message}
              </p>
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={handleReset}>
                Try Again
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
