import { useEffect, useState } from 'react';
import { Check, X, Loader2, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';
import { adminApi } from '@/api/admin';
import type { User } from '@/types/auth';

export function PendingUsersPanel() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      const data = await adminApi.listPendingUsers();
      setUsers(data);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to load pending users',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingUsers();
  }, []);

  const handleApprove = async (userId: string, email: string) => {
    setActionLoading(userId);
    try {
      await adminApi.approveUser(userId);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
      toast({
        title: 'User approved',
        description: `${email} has been approved and can now sign in.`,
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to approve user',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (userId: string, email: string) => {
    setActionLoading(userId);
    try {
      await adminApi.rejectUser(userId);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
      toast({
        title: 'User rejected',
        description: `${email} has been rejected.`,
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to reject user',
      });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          <CardTitle className="text-xl">
            Pending Users
            {users.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {users.length}
              </Badge>
            )}
          </CardTitle>
        </div>
        <CardDescription>Users awaiting approval to access the platform</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : users.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No pending users at this time.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Platforms</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.email}</TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {user.platforms.length > 0 ? (
                        user.platforms.map((p) => (
                          <Badge key={p} variant="outline">
                            {p}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground text-sm">All</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex gap-2 justify-end">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-green-600 hover:text-green-700 hover:bg-green-50"
                        disabled={actionLoading === user.id}
                        onClick={() => handleApprove(user.id, user.email)}
                      >
                        {actionLoading === user.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Check className="h-4 w-4 mr-1" />
                        )}
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        disabled={actionLoading === user.id}
                        onClick={() => handleReject(user.id, user.email)}
                      >
                        {actionLoading === user.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <X className="h-4 w-4 mr-1" />
                        )}
                        Reject
                      </Button>
                    </div>
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
