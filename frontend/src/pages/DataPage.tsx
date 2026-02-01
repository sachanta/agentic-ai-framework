import { Link } from 'react-router-dom';
import { Database, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ROUTES } from '@/utils/constants';

export function DataPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Data Management</h1>
        <p className="text-muted-foreground">Manage your databases and data stores</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link to={ROUTES.WEAVIATE}>
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-6 w-6 text-purple-500" />
                Weaviate
              </CardTitle>
              <CardDescription>
                Vector database for semantic search and embeddings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Manage collections and schemas</li>
                <li>• Browse and search documents</li>
                <li>• Perform vector similarity search</li>
                <li>• Bulk import/export data</li>
              </ul>
            </CardContent>
          </Card>
        </Link>

        <Link to={ROUTES.MONGODB}>
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-6 w-6 text-green-500" />
                MongoDB
              </CardTitle>
              <CardDescription>
                Document database for structured data storage
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Browse databases and collections</li>
                <li>• Query and filter documents</li>
                <li>• View and edit records</li>
                <li>• Import/export collections</li>
              </ul>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}

export default DataPage;
