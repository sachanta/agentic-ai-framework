import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CollectionList } from '@/components/data/weaviate/CollectionList';
import { DocumentBrowser } from '@/components/data/weaviate/DocumentBrowser';
import { VectorSearch } from '@/components/data/weaviate/VectorSearch';
import { BulkImport } from '@/components/data/weaviate/BulkImport';
import { PDFUpload } from '@/components/data/weaviate/PDFUpload';

export function WeaviatePage() {
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Weaviate</h1>
        <p className="text-muted-foreground">Vector database management</p>
      </div>

      <Tabs defaultValue="collections">
        <TabsList>
          <TabsTrigger value="collections">Collections</TabsTrigger>
          <TabsTrigger value="documents" disabled={!selectedCollection}>
            Documents
          </TabsTrigger>
          <TabsTrigger value="search" disabled={!selectedCollection}>
            Vector Search
          </TabsTrigger>
          <TabsTrigger value="import" disabled={!selectedCollection}>
            Bulk Import
          </TabsTrigger>
          <TabsTrigger value="pdf-upload">PDF Upload</TabsTrigger>
        </TabsList>

        <TabsContent value="collections" className="mt-4">
          <CollectionList onSelectCollection={setSelectedCollection} />
          {selectedCollection && (
            <p className="text-sm text-muted-foreground mt-2">
              Selected: <strong>{selectedCollection}</strong> - Use the tabs above to browse documents, search, or import data
            </p>
          )}
        </TabsContent>

        <TabsContent value="documents" className="mt-4">
          {selectedCollection && <DocumentBrowser collectionName={selectedCollection} />}
        </TabsContent>

        <TabsContent value="search" className="mt-4">
          {selectedCollection && <VectorSearch collection={selectedCollection} />}
        </TabsContent>

        <TabsContent value="import" className="mt-4">
          {selectedCollection && <BulkImport collectionName={selectedCollection} />}
        </TabsContent>

        <TabsContent value="pdf-upload" className="mt-4">
          <PDFUpload />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default WeaviatePage;
