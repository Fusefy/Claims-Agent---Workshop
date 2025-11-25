import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Clock, XCircle, MinusCircle, PlusCircle, Eye, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { claimsApiNew, ProposedClaim, ClaimStatistics, getStatusBadgeVariant, formatDate } from '@/lib/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<ClaimStatistics | null>(null);
  const [recentClaims, setRecentClaims] = useState<ProposedClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Get current user's ID from token or stored data
        const token = localStorage.getItem('auth_token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Fetch statistics
        const statsData = await claimsApiNew.getClaimStatistics();
        setStats(statsData);

        // Fetch recent claims (assuming customer_id is stored or extracted from token)
        // For now, we'll get all claims and limit to 5
        const claimsData = await claimsApiNew.getAllClaims({ limit: 5 });
        // Ensure claimsData is an array
        setRecentClaims(Array.isArray(claimsData) ? claimsData : []);

      } catch (err: any) {
        console.error('Error fetching dashboard data:', err);
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Dashboard</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </div>
      </div>
    );
  }

  const statsData = [
    { label: 'Total Claims', value: stats?.total || 0, icon: null, color: 'text-foreground' },
    { label: 'Approved', value: stats?.approved || 0, icon: CheckCircle, color: 'text-success' },
    { label: 'Pending', value: stats?.pending || 0, icon: Clock, color: 'text-warning' },
    { label: 'Denied', value: stats?.denied || 0, icon: XCircle, color: 'text-destructive' },
    { label: 'Withdrawn', value: stats?.withdrawn || 0, icon: MinusCircle, color: 'text-muted-foreground' },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground">Dashboard</h1>
          <p className="mt-1 text-base text-muted-foreground">Overview of your reimbursement claims</p>
        </div>
        <Button onClick={() => navigate('/claims/new')} className="gap-2 rounded-xl px-6 py-5 shadow-sm hover:shadow-md smooth-transition">
          <PlusCircle className="h-5 w-5" />
          New Claim
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-5">
        {statsData.map((stat) => (
          <Card key={stat.label} className="card-hover rounded-2xl border-0 shadow-sm">
            <CardContent className="p-6">
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                  {stat.icon && (
                    <div className={`rounded-xl bg-gradient-to-br p-2 ${
                      stat.label === 'Approved' ? 'from-green-50 to-green-100' :
                      stat.label === 'Pending' ? 'from-yellow-50 to-yellow-100' :
                      stat.label === 'Denied' ? 'from-red-50 to-red-100' :
                      'from-gray-50 to-gray-100'
                    }`}>
                      <stat.icon className={`h-5 w-5 ${stat.color}`} />
                    </div>
                  )}
                </div>
                <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Claims Table */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader className="border-b bg-muted/30 px-6 py-4">
          <CardTitle className="text-xl">Recent Claims</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {recentClaims.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center">
              <p className="text-lg font-semibold text-muted-foreground">No claims yet</p>
              <p className="mt-1 text-sm text-muted-foreground">Start by creating your first claim</p>
              <Button onClick={() => navigate('/claims/new')} className="mt-6 rounded-xl">
                Create Claim
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/20">
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Claim ID</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Name</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Type</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Amount</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Date</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {recentClaims.map((claim) => (
                    <tr key={claim.claim_id} className="smooth-transition hover:bg-muted/30">
                      <td className="px-6 py-4 text-sm font-medium text-foreground">{claim.claim_id}</td>
                      <td className="px-6 py-4 text-sm text-foreground">
                        {claim.claim_name || <span className="text-muted-foreground italic">No name</span>}
                      </td>
                      <td className="px-6 py-4 text-sm text-foreground">{claim.claim_type || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm font-semibold text-foreground">
                                            <p className="text-sm font-semibold text-foreground">
                      ${(claim.claim_amount || 0).toLocaleString('en-US')}
                    </p>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {formatDate(claim.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        <Badge
                          variant={getStatusBadgeVariant(claim.claim_status)}
                          className="rounded-full px-3 py-1 text-xs font-medium"
                        >
                          {claim.claim_status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/claims/${claim.claim_id}`)}
                          className="gap-2 rounded-lg hover:bg-primary/10 hover:text-primary smooth-transition"
                        >
                          <Eye className="h-4 w-4" />
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
