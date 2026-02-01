import { useState } from 'react';
import { ExternalLink, Maximize2, Minimize2, Copy, Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/store/authStore';
import { API_URL } from '@/utils/constants';

export function SwaggerEmbed() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [copied, setCopied] = useState(false);
  const { token } = useAuthStore();

  const docsUrl = `${API_URL}/docs`;

  const handleCopyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleOpenNewTab = () => {
    window.open(docsUrl, '_blank');
  };

  return (
    <div className={isFullscreen ? 'fixed inset-0 z-50 bg-background' : 'space-y-4'}>
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-bold">API Explorer</h2>
          <Badge variant="outline">FastAPI Swagger UI</Badge>
        </div>
        <div className="flex items-center gap-2">
          {token && (
            <Card className="p-2">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Auth Token:</span>
                <code className="bg-muted px-2 py-1 rounded text-xs max-w-[200px] truncate">
                  {token.slice(0, 20)}...
                </code>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCopyToken}>
                  {copied ? (
                    <Check className="h-3 w-3 text-green-500" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              </div>
            </Card>
          )}
          <Button variant="outline" size="sm" onClick={handleOpenNewTab}>
            <ExternalLink className="mr-2 h-4 w-4" />
            Open in New Tab
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
          >
            {isFullscreen ? (
              <>
                <Minimize2 className="mr-2 h-4 w-4" />
                Exit Fullscreen
              </>
            ) : (
              <>
                <Maximize2 className="mr-2 h-4 w-4" />
                Fullscreen
              </>
            )}
          </Button>
        </div>
      </div>

      <div className={isFullscreen ? 'h-[calc(100vh-80px)]' : 'h-[calc(100vh-200px)]'}>
        <iframe
          src={docsUrl}
          title="API Documentation"
          className="w-full h-full border-0"
          sandbox="allow-same-origin allow-scripts allow-forms"
        />
      </div>
    </div>
  );
}
