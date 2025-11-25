import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Save, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '@/contexts/UserContext';
import { formatDate } from '@/lib/api';

interface ProfileProps {
  onLogout: () => void;
}

export default function Profile({ onLogout }: ProfileProps) {
  const { toast } = useToast();
  const navigate = useNavigate();
  const { user } = useUser();

  const handleSave = () => {
    toast({
      title: 'Settings Updated',
      description: 'Your profile and preferences have been saved successfully.',
    });
  };

  const handleLogout = () => {
    onLogout();
    navigate('/login');
    toast({
      title: 'Logged Out',
      description: 'You have been successfully logged out.',
    });
  };

  return (
    <div className="container mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight text-foreground">Profile & Settings</h1>
        <p className="mt-1 text-base text-muted-foreground">
          Manage your account information and preferences
        </p>
      </div>

      {/* User Profile */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader className="border-b bg-muted/30 px-6 py-4">
          <CardTitle className="text-xl">Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 p-6">
          {!user && (
            <div className="rounded-lg bg-warning/10 border border-warning/30 p-4 text-sm text-warning">
              User data not loaded. Please try logging out and back in.
            </div>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input 
                id="username" 
                defaultValue={user?.username || ''} 
                className="rounded-xl bg-muted/50 focus:bg-background smooth-transition theme-transition" 
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input 
                id="email" 
                type="email" 
                defaultValue={user?.email || ''} 
                className="rounded-xl bg-muted/50 focus:bg-background smooth-transition theme-transition" 
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="role">Role</Label>
            <Input 
              id="role" 
              defaultValue={user?.role || ''} 
              disabled 
              className="rounded-xl bg-muted/30 theme-transition" 
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="userId">User ID</Label>
            <Input 
              id="userId" 
              defaultValue={user?.user_id?.toString() || ''} 
              disabled 
              className="rounded-xl bg-muted/30 theme-transition" 
            />
          </div>
          {user?.created_at && (
            <div className="space-y-2">
              <Label htmlFor="created">Member Since</Label>
              <Input 
                id="created" 
                defaultValue={formatDate(user.created_at, 'long')} 
                disabled 
                className="rounded-xl bg-muted/30 theme-transition" 
              />
            </div>
          )}
          {user?.google_id && (
            <div className="rounded-lg bg-success/10 border border-success/30 p-4">
              <p className="text-sm text-success font-medium">✓ Connected with Google OAuth</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-between">
        <Button 
          onClick={handleLogout} 
          variant="outline"
          className="gap-2 rounded-xl px-6 py-5 border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive shadow-sm smooth-transition theme-transition"
        >
          <LogOut className="h-5 w-5" />
          Logout
        </Button>
        <Button onClick={handleSave} className="gap-2 rounded-xl px-6 py-5 shadow-sm hover:shadow-md smooth-transition">
          <Save className="h-5 w-5" />
          Save Changes
        </Button>
      </div>
    </div>
  );
}
