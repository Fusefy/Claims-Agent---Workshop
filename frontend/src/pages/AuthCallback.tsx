import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { useUser } from '@/contexts/UserContext';
import { authApi } from '@/lib/api';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setUser } = useUser();

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token');
      
      if (token) {
        // Store JWT token in localStorage
        localStorage.setItem('auth_token', token);
        
        // Verify token and get user data
        try {
          const userData = await authApi.verifyToken(token);
          setUser(userData);
          
          console.log('Authentication successful, redirecting to dashboard...');
          
          // Redirect to dashboard
          setTimeout(() => {
            navigate('/', { replace: true });
          }, 500);
        } catch (error) {
          console.error('Token verification failed:', error);
          navigate('/login', { replace: true });
        }
      } else {
        console.error('No token received from OAuth callback');
        // Redirect to login on error
        navigate('/login', { replace: true });
      }
    };

    handleCallback();
  }, [searchParams, navigate, setUser]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="text-lg font-medium">Completing authentication...</p>
            <p className="text-sm text-muted-foreground">Please wait while we redirect you.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
