import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Eye, Search, Filter, PlusCircle, Loader2, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { claimsApiNew, ProposedClaim, getStatusBadgeVariant, formatDate } from '@/lib/api';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function Claims() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [claims, setClaims] = useState<ProposedClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClaims = async () => {
      try {
        setLoading(true);
        // Fetch all claims for the user
        const claimsData = await claimsApiNew.getAllClaims();
        // Ensure claimsData is an array
        setClaims(Array.isArray(claimsData) ? claimsData : []);
      } catch (err: any) {
        console.error('Error fetching claims:', err);
        setError(err.message || 'Failed to load claims');
      } finally {
        setLoading(false);
      }
    };

    fetchClaims();
  }, []);

  // Filter claims
  const filteredClaims = claims.filter((claim) => {
    const matchesSearch = 
      claim.claim_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (claim.claim_name?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
      (claim.claim_type?.toLowerCase() || '').includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || 
      claim.claim_status.toLowerCase().includes(statusFilter.toLowerCase());
    
    const matchesCategory = categoryFilter === 'all' || 
      (claim.claim_type?.toLowerCase() || '') === categoryFilter.toLowerCase();
    
    return matchesSearch && matchesStatus && matchesCategory;
  });

  // Get unique categories
  const categories = Array.from(new Set(claims.map((c) => c.claim_type).filter(Boolean)));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading claims...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Claims</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground">My Claims</h1>
          <p className="mt-1 text-base text-muted-foreground">
            View and manage all your reimbursement claims
          </p>
        </div>
        <Button onClick={() => navigate('/claims/new')} className="gap-2 rounded-xl px-6 py-5 shadow-sm hover:shadow-md smooth-transition">
          <PlusCircle className="h-5 w-5" />
          New Claim
        </Button>
      </div>

      {/* Filters */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-3 md:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by claim ID, name, or type..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-11 rounded-xl bg-muted/50 focus:bg-background smooth-transition theme-transition"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className={`w-full md:w-[180px] rounded-xl smooth-transition theme-transition ${statusFilter !== 'all' ? 'bg-primary/10 border-primary/30 font-medium' : 'bg-muted/50'}`}>
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="denied">Denied</SelectItem>
                  <SelectItem value="withdrawn">Withdrawn</SelectItem>
                </SelectContent>
              </Select>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className={`w-full md:w-[180px] rounded-xl smooth-transition theme-transition ${categoryFilter !== 'all' ? 'bg-primary/10 border-primary/30 font-medium' : 'bg-muted/50'}`}>
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {(searchQuery || statusFilter !== 'all' || categoryFilter !== 'all') && (
              <div className="flex items-center justify-between rounded-xl bg-primary/10 px-4 py-3 border border-primary/20 theme-transition">
                <p className="text-sm font-medium text-primary">
                  {searchQuery && `Search: "${searchQuery}"`}
                  {searchQuery && (statusFilter !== 'all' || categoryFilter !== 'all') && ' • '}
                  {statusFilter !== 'all' && `Status: ${statusFilter}`}
                  {statusFilter !== 'all' && categoryFilter !== 'all' && ' • '}
                  {categoryFilter !== 'all' && `Category: ${categoryFilter}`}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('');
                    setStatusFilter('all');
                    setCategoryFilter('all');
                  }}
                  className="text-xs text-primary hover:text-primary hover:bg-primary/20 rounded-lg theme-transition"
                >
                  Clear filters
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Claims List */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader className="border-b bg-muted/30 px-6 py-4">
          <CardTitle className="text-xl">
            {filteredClaims.length} Claim{filteredClaims.length !== 1 ? 's' : ''}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {filteredClaims.length === 0 ? (
            <div className="flex min-h-[300px] flex-col items-center justify-center text-center p-6">
              <p className="text-lg font-semibold text-muted-foreground">No claims found</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {searchQuery || statusFilter !== 'all' || categoryFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Start by creating your first claim'}
              </p>
              {!searchQuery && statusFilter === 'all' && categoryFilter === 'all' && (
                <Button onClick={() => navigate('/claims/new')} className="mt-6 rounded-xl">
                  Create Claim
                </Button>
              )}
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
                  {filteredClaims.map((claim) => (
                    <tr key={claim.claim_id} className="smooth-transition hover:bg-muted/30">
                      <td className="px-6 py-4 text-sm font-medium text-foreground">{claim.claim_id}</td>
                      <td className="px-6 py-4 text-sm text-foreground">
                        {claim.claim_name || <span className="text-muted-foreground italic">No name</span>}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="outline" className="rounded-full">{claim.claim_type || 'N/A'}</Badge>
                      </td>
                      <td className="px-6 py-4 text-sm font-semibold text-foreground">
                        ${(claim.claim_amount || 0).toLocaleString('en-US')}
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {formatDate(claim.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={getStatusBadgeVariant(claim.claim_status)}
                            className="rounded-full px-3 py-1 text-xs font-medium"
                          >
                            {claim.claim_status}
                          </Badge>
                          {claim.guardrail_summary?.hitl_flag && (
                            <Badge variant="warning" className="rounded-full px-2 py-1 text-xs">
                              HITL
                            </Badge>
                          )}
                        </div>
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
