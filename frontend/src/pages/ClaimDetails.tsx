import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Download, FileText, TrendingUp, AlertCircle, Eye, EyeOff, Loader2, Shield, CheckCircle2, Clock } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { claimsApiNew, ProposedClaim, ClaimHistory, getStatusBadgeVariant, formatDate } from '@/lib/api';

export default function ClaimDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showPolicyId, setShowPolicyId] = useState(false);
  const [claim, setClaim] = useState<ProposedClaim | null>(null);
  const [history, setHistory] = useState<ClaimHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    const fetchClaimData = async () => {
      if (!id) {
        setError('No claim ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        
        // Fetch claim details
        const claimData = await claimsApiNew.getClaimById(id);
        setClaim(claimData);

        // Fetch claim history
        try {
          const historyData = await claimsApiNew.getClaimHistory(id);
          setHistory(historyData);
        } catch (histErr) {
          console.warn('Could not fetch claim history:', histErr);
          // Non-critical, continue without history
        }

      } catch (err: any) {
        console.error('Error fetching claim details:', err);
        setError(err.message || 'Failed to load claim details');
      } finally {
        setLoading(false);
      }
    };

    fetchClaimData();
  }, [id]);

  const getStatusColor = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized.includes('approved')) {
      return 'bg-success/10 text-success border-success/20';
    }
    if (normalized.includes('pending')) {
      return 'bg-warning/10 text-warning border-warning/20';
    }
    if (normalized.includes('denied') || normalized.includes('rejected')) {
      return 'bg-destructive/10 text-destructive border-destructive/20';
    }
    return 'bg-muted text-muted-foreground border-border';
  };

  const handleWithdraw = async () => {
    if (!claim || !id) return;

    setUpdating(true);
    try {
      await claimsApiNew.updateClaimStatus(id, 'Withdrawn', 'User requested withdrawal');
      
      toast({
        title: 'Claim Withdrawn',
        description: 'Your claim has been withdrawn successfully.',
        variant: 'destructive',
      });
      
      setTimeout(() => navigate('/claims'), 1500);
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.message || 'Failed to withdraw claim',
        variant: 'destructive',
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleDownload = (docName: string) => {
    toast({
      title: 'Download Started',
      description: `Downloading ${docName}...`,
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading claim details...</p>
        </div>
      </div>
    );
  }

  if (error || !claim) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="text-2xl font-bold">Claim Not Found</h2>
          <p className="mb-4 text-muted-foreground">{error || "The claim you're looking for doesn't exist."}</p>
          <Button onClick={() => navigate('/claims')}>Back to Claims</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/claims')} className="rounded-xl hover:bg-primary/10">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            {claim.claim_name || claim.claim_type || 'Claim Details'}
          </h1>
          <p className="mt-1 text-sm font-medium text-muted-foreground">Claim ID: #{claim.claim_id}</p>
          {claim.claim_name && claim.claim_type && (
            <p className="mt-0.5 text-xs text-muted-foreground">Type: {claim.claim_type}</p>
          )}
        </div>
      </div>

      {/* Status Banner */}
      <Card className={`border-2 rounded-2xl shadow-sm ${getStatusColor(claim.claim_status)}`}>
        <CardContent className="flex items-center justify-between px-8 py-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Current Status</p>
            <p className="mt-1 text-3xl font-bold capitalize">{claim.claim_status}</p>
            {claim.guardrail_summary?.hitl_flag && (
              <Badge variant="warning" className="mt-2 rounded-full">
                Under Human Review
              </Badge>
            )}
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Claim Amount</p>
            <p className="mt-1 text-3xl font-bold">${(claim.claim_amount || 0).toLocaleString('en-US')}</p>
          </div>
          {claim.approved_amount > 0 && (
            <div className="text-right">
              <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Approved Amount</p>
              <p className="mt-1 text-3xl font-bold text-success">
                ${claim.approved_amount.toLocaleString('en-US')}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                ({((claim.approved_amount / (claim.claim_amount || 1)) * 100).toFixed(1)}% approved)
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Extracted Claim Details */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader className="border-b bg-muted/30 px-6 py-4">
          <CardTitle className="text-xl font-bold text-primary">Claim Information</CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Customer ID */}
            <div className="space-y-2">
              <Label htmlFor="customerId" className="text-sm text-muted-foreground">Customer ID</Label>
              <Input 
                id="customerId"
                value={claim.customer_id}
                readOnly
                className="bg-muted/50 border-border"
              />
            </div>

            {/* Policy ID with Eye Toggle */}
            {claim.policy_id && (
              <div className="space-y-2">
                <Label htmlFor="policyId" className="text-sm text-muted-foreground">Policy ID</Label>
                <div className="relative">
                  <Input 
                    id="policyId"
                    value={showPolicyId ? claim.policy_id : `••••••••••••${claim.policy_id.slice(-4)}`}
                    readOnly
                    className="bg-muted/50 border-border pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    onClick={() => setShowPolicyId(!showPolicyId)}
                  >
                    {showPolicyId ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                </div>
              </div>
            )}

            {/* Date of Service */}
            {claim.date_of_service && (
              <div className="space-y-2">
                <Label htmlFor="dateOfService" className="text-sm text-muted-foreground">Date of Service</Label>
                <Input 
                  id="dateOfService"
                  value={formatDate(claim.date_of_service, 'long')}
                  readOnly
                  className="bg-muted/50 border-border"
                />
              </div>
            )}

            {/* Claim Type */}
            {claim.claim_type && (
              <div className="space-y-2">
                <Label htmlFor="claimType" className="text-sm text-muted-foreground">Claim Type</Label>
                <Input 
                  id="claimType"
                  value={claim.claim_type}
                  readOnly
                  className="bg-muted/50 border-border"
                />
              </div>
            )}

            {/* Network Status */}
            {claim.network_status && (
              <div className="space-y-2">
                <Label htmlFor="networkStatus" className="text-sm text-muted-foreground">Network Status</Label>
                <Input 
                  id="networkStatus"
                  value={claim.network_status}
                  readOnly
                  className="bg-muted/50 border-border"
                />
              </div>
            )}

            {/* Payment Status */}
            <div className="space-y-2">
              <Label htmlFor="paymentStatus" className="text-sm text-muted-foreground">Payment Status</Label>
              <Input 
                id="paymentStatus"
                value={claim.payment_status}
                readOnly
                className="bg-muted/50 border-border"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Timeline & AI */}
        <div className="space-y-6 lg:col-span-2">
          {/* Timeline */}
          {history.length > 0 && (
            <Card className="rounded-2xl border-0 shadow-sm">
              <CardHeader className="border-b bg-muted/30 px-6 py-4">
                <CardTitle className="text-xl">Claim Timeline</CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-6">
                  {history.map((event, index) => (
                    <div key={event.history_id} className="flex gap-4">
                      <div className="relative flex flex-col items-center">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-primary bg-gradient-to-br from-primary/10 to-primary/5 shadow-sm">
                          <span className="text-sm font-bold text-primary">{index + 1}</span>
                        </div>
                        {index < history.length - 1 && (
                          <div className="h-full w-0.5 bg-gradient-to-b from-primary/30 to-transparent" />
                        )}
                      </div>
                      <div className="flex-1 pb-6">
                        <h3 className="font-semibold text-foreground">
                          {event.old_status} → {event.new_status}
                        </h3>
                        {event.change_reason && (
                          <p className="mt-1 text-sm text-muted-foreground">{event.change_reason}</p>
                        )}
                        <p className="mt-2 text-xs font-medium text-muted-foreground">
                          {formatDate(event.timestamp, 'long')} by {event.changed_by} ({event.role})
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* AI Analysis - Using ai_reasoning and guardrail_summary */}
          {(claim.guardrail_summary || claim.ai_reasoning) && (
            <Card className="rounded-2xl border-0 shadow-sm overflow-hidden">
              <div className="h-1 bg-gradient-to-r from-primary via-blue-500 to-primary" />
              <CardHeader className="border-b bg-gradient-to-br from-primary/5 to-transparent px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                    <TrendingUp className="h-5 w-5 text-primary" />
                  </div>
                  <CardTitle className="text-xl">AI Analysis</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4 p-6">
                {/* Primary AI Reasoning */}
                {claim.ai_reasoning && (
                  <div className="rounded-xl bg-gradient-to-br from-primary/5 to-primary/10 p-4 border border-primary/20">
                    <div className="flex items-start gap-3">
                      <Shield className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold mb-2 text-primary">AI Decision Reasoning:</h4>
                        <p className="text-sm leading-relaxed text-foreground">{claim.ai_reasoning}</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Detailed Guardrail Summary */}
                {claim.guardrail_summary && typeof claim.guardrail_summary === 'object' && Object.keys(claim.guardrail_summary).length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                      <Shield className="h-4 w-4 text-primary" />
                      Fraud Detection & Analysis:
                    </h4>
                    
                    {/* Display fraud detection info in 2-column grid */}
                    <div className="grid grid-cols-2 gap-3">
                      {claim.guardrail_summary.fraud_status && (
                        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border">
                          <span className="text-sm font-medium text-muted-foreground">Fraud Status</span>
                          <Badge 
                            variant={claim.guardrail_summary.fraud_status === 'No Fraud' ? 'success' : 'destructive'}
                            className="rounded-full"
                          >
                            {claim.guardrail_summary.fraud_status}
                          </Badge>
                        </div>
                      )}
                      
                      {/* Confidence score removed */}
                      
                      {claim.guardrail_summary.hitl_flag !== undefined && (
                        <div className="col-span-2 flex items-center justify-between p-3 bg-muted/50 rounded-lg border">
                          <span className="text-sm font-medium text-muted-foreground">Human Review Required</span>
                          <Badge 
                            variant={claim.guardrail_summary.hitl_flag ? 'warning' : 'success'}
                            className="rounded-full"
                          >
                            {claim.guardrail_summary.hitl_flag ? 'Yes' : 'No'}
                          </Badge>
                        </div>
                      )}
                      
                      {claim.guardrail_summary.fraud_reason && (
                        <div className="col-span-2 p-3 bg-muted/50 rounded-lg border">
                          <span className="text-sm font-medium text-muted-foreground block mb-1">Fraud Detection Reason:</span>
                          <p className="text-sm text-foreground">{claim.guardrail_summary.fraud_reason}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Show message if no AI analysis data */}
                {!claim.ai_reasoning && (!claim.guardrail_summary || Object.keys(claim.guardrail_summary).length === 0) && (
                  <div className="text-center py-4">
                    <p className="text-sm text-muted-foreground">No AI analysis data available for this claim.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Remittance & Coverage Analysis */}
          {claim.claim_status === 'Approved' && claim.approved_amount > 0 && (
            <Card className="rounded-2xl border-0 shadow-sm overflow-hidden">
              <div className="h-1 bg-gradient-to-r from-success via-green-500 to-success" />
              <CardHeader className="border-b bg-gradient-to-br from-success/5 to-transparent px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-success/10">
                    <CheckCircle2 className="h-5 w-5 text-success" />
                  </div>
                  <CardTitle className="text-xl">Remittance & Coverage Analysis</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4 p-6">
                {/* Approval Summary */}
                <div className="rounded-xl bg-gradient-to-br from-success/5 to-success/10 p-4 border border-success/20">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Original Amount</p>
                      <p className="text-xl font-bold text-foreground">
                        ${(claim.claim_amount || 0).toLocaleString('en-US')}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Approved Amount</p>
                      <p className="text-xl font-bold text-success">
                        ${claim.approved_amount.toLocaleString('en-US')}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Coverage Rate</p>
                      <p className="text-xl font-bold text-success">
                        {((claim.approved_amount / (claim.claim_amount || 1)) * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Network Status</p>
                      <Badge variant={claim.network_status?.includes('In-Network') ? 'success' : 'warning'}>
                        {claim.network_status || 'Unknown'}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* AI Reasoning for Approval */}
                {claim.ai_reasoning && (
                  <div className="p-4 bg-muted/50 rounded-lg border">
                    <p className="text-sm font-medium text-muted-foreground mb-2">Approval Reasoning:</p>
                    <p className="text-sm text-foreground">{claim.ai_reasoning}</p>
                  </div>
                )}

                {/* Payment Timeline */}
                <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-success" />
                    <div>
                      <p className="text-sm font-medium">Expected Payment</p>
                      <p className="text-xs text-muted-foreground">Within 5-7 business days</p>
                    </div>
                  </div>
                  <Badge variant="success" className="rounded-full">
                    {claim.payment_status}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Actions */}
        <div className="space-y-6">
          {/* Actions */}
          <Card className="rounded-2xl border-0 shadow-sm">
            <CardHeader className="border-b bg-muted/30 px-6 py-4">
              <CardTitle className="text-xl">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-6">
              {claim.claim_status.toLowerCase().includes('pending') && (
                <Button 
                  variant="destructive" 
                  className="w-full rounded-xl shadow-sm" 
                  onClick={handleWithdraw}
                  disabled={updating}
                >
                  {updating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Withdrawing...
                    </>
                  ) : (
                    'Withdraw Claim'
                  )}
                </Button>
              )}
              <Button variant="outline" className="w-full rounded-xl" onClick={() => navigate('/claims')}>
                Back to Claims
              </Button>
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card className="rounded-2xl border-0 shadow-sm">
            <CardHeader className="border-b bg-muted/30 px-6 py-4">
              <CardTitle className="text-xl">Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-6 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created:</span>
                <span className="font-medium">{formatDate(claim.created_at, 'long')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Updated:</span>
                <span className="font-medium">{formatDate(claim.updated_at, 'long')}</span>
              </div>
              {claim.error_type && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Error Type:</span>
                  <span className="font-medium text-destructive">{claim.error_type}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
