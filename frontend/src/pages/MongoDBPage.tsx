import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CollectionBrowser } from '@/components/data/mongodb/CollectionBrowser';
import { DocumentViewer } from '@/components/data/mongodb/DocumentViewer';
import { QueryBuilder } from '@/components/data/mongodb/QueryBuilder';
import { ImportExport } from '@/components/data/mongodb/ImportExport';

export function MongoDBPage() {
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  const handleSelectCollection = (_database: string, collection: string) => {
    setSelectedCollection(collection);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">MongoDB</h1>
        <p className="text-muted-foreground">Document database management</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <CollectionBrowser onSelectCollection={handleSelectCollection} />
        </div>
        <div className="lg:col-span-3">
          {selectedCollection ? (
            <Tabs defaultValue="documents">
              <TabsList>
                <TabsTrigger value="documents">Documents</TabsTrigger>
                <TabsTrigger value="query">Query Builder</TabsTrigger>
                <TabsTrigger value="import-export">Import / Export</TabsTrigger>
              </TabsList>

              <TabsContent value="documents" className="mt-4">
                <DocumentViewer collectionName={selectedCollection} />
              </TabsContent>

              <TabsContent value="query" className="mt-4">
                <QueryBuilder collection={selectedCollection} />
              </TabsContent>

              <TabsContent value="import-export" className="mt-4">
                <ImportExport collectionName={selectedCollection} />
              </TabsContent>
            </Tabs>
          ) : (
            <div className="flex items-center justify-center h-64 border rounded-lg">
              <p className="text-muted-foreground">Select a collection to manage</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MongoDBPage;
