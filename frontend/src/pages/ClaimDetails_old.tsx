import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { mockClaims } from '@/lib/mockData';
import { ArrowLeft, Download, FileText, TrendingUp, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function ClaimDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showPolicyId, setShowPolicyId] = useState(false);
  
  const claim = mockClaims.find((c) => c.id === id);
  
  // Mock extracted claim data
  const extractedData = {
    vendorName: 'HCA Healthcare',
    policyId: '1223',
    transactionDate: '2025-10-22',
    totalAmount: '85.00 USD',
    claimType: 'Medical',
    lineItems: [
      { description: 'Lab Work', amount: '85.00' }
    ]
  };

  if (!claim) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="text-2xl font-bold">Claim Not Found</h2>
          <p className="mb-4 text-muted-foreground">The claim you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-success/10 text-success border-success/20';
      case 'pending':
        return 'bg-warning/10 text-warning border-warning/20';
      case 'denied':
        return 'bg-destructive/10 text-destructive border-destructive/20';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  const handleWithdraw = () => {
    toast({
      title: 'Claim Withdrawn',
      description: 'Your claim has been withdrawn successfully.',
      variant: 'destructive',
    });
    setTimeout(() => navigate('/claims'), 1500);
  };

  const handleDownload = (docName: string) => {
    toast({
      title: 'Download Started',
      description: `Downloading ${docName}...`,
    });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/claims')} className="rounded-xl hover:bg-primary/10">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">{claim.claimName}</h1>
          <p className="mt-1 text-sm font-medium text-muted-foreground">Claim ID: #{claim.id}</p>
        </div>
      </div>

      {/* Status Banner */}
      <Card className={`border-2 rounded-2xl shadow-sm ${getStatusColor(claim.status)}`}>
        <CardContent className="flex items-center justify-between px-8 py-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Current Status</p>
            <p className="mt-1 text-3xl font-bold capitalize">{claim.status}</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Amount</p>
            <p className="mt-1 text-3xl font-bold">₹{claim.amount.toLocaleString('en-IN')}</p>
          </div>
        </CardContent>
      </Card>

      {/* Extracted Claim Details */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader className="border-b bg-muted/30 px-6 py-4">
          <CardTitle className="text-xl font-bold text-primary">Extracted Claim Details</CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          {/* Main Fields Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Vendor Name */}
            <div className="space-y-2">
              <Label htmlFor="vendorName" className="text-sm text-muted-foreground">Vendor Name</Label>
              <Input 
                id="vendorName"
                value={extractedData.vendorName}
                readOnly
                className="bg-muted/50 border-border"
              />
            </div>

            {/* Policy ID with Eye Toggle */}
            <div className="space-y-2">
              <Label htmlFor="policyId" className="text-sm text-muted-foreground">Policy ID</Label>
              <div className="relative">
                <Input 
                  id="policyId"
                  value={showPolicyId ? extractedData.policyId : `••••••••••••${extractedData.policyId}`}
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

            {/* Transaction Date */}
            <div className="space-y-2">
              <Label htmlFor="transactionDate" className="text-sm text-muted-foreground">Transaction Date</Label>
              <Input 
                id="transactionDate"
                value={extractedData.transactionDate}
                readOnly
                className="bg-muted/50 border-border"
              />
            </div>

            {/* Total Amount */}
            <div className="space-y-2">
              <Label htmlFor="totalAmount" className="text-sm text-muted-foreground">Total Amount</Label>
              <Input 
                id="totalAmount"
                value={extractedData.totalAmount}
                readOnly
                className="bg-muted/50 border-border"
              />
            </div>

            {/* Claim Type */}
            <div className="space-y-2">
              <Label htmlFor="claimType" className="text-sm text-muted-foreground">Claim Type</Label>
              <Input 
                id="claimType"
                value={extractedData.claimType}
                readOnly
                className="bg-muted/50 border-border"
              />
            </div>
          </div>

          {/* Line Items Section */}
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-foreground">Line Items</h3>
            <div className="rounded-lg border border-border overflow-hidden">
              <div className="bg-muted/50 px-4 py-3 grid grid-cols-2 gap-4 border-b border-border">
                <div className="text-sm font-medium text-muted-foreground">Description</div>
                <div className="text-sm font-medium text-muted-foreground">Amount</div>
              </div>
              {extractedData.lineItems.map((item, index) => (
                <div key={index} className="px-4 py-3 grid grid-cols-2 gap-4 bg-card hover:bg-muted/30 smooth-transition">
                  <div className="text-sm text-foreground">{item.description}</div>
                  <div className="text-sm text-foreground">{item.amount}</div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Timeline & AI */}
        <div className="space-y-6 lg:col-span-2">
          {/* Timeline */}
          <Card className="rounded-2xl border-0 shadow-sm">
            <CardHeader className="border-b bg-muted/30 px-6 py-4">
              <CardTitle className="text-xl">Claim Timeline</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                {claim.timeline.map((event, index) => (
                  <div key={event.id} className="flex gap-4">
                    <div className="relative flex flex-col items-center">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-primary bg-gradient-to-br from-primary/10 to-primary/5 shadow-sm">
                        <span className="text-sm font-bold text-primary">{index + 1}</span>
                      </div>
                      {index < claim.timeline.length - 1 && (
                        <div className="h-full w-0.5 bg-gradient-to-b from-primary/30 to-transparent" />
                      )}
                    </div>
                    <div className="flex-1 pb-6">
                      <h3 className="font-semibold text-foreground">{event.status}</h3>
                      <p className="mt-1 text-sm text-muted-foreground">{event.description}</p>
                      <p className="mt-2 text-xs font-medium text-muted-foreground">
                        {new Date(event.date).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric',
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* AI Recommendation */}
          {claim.aiRecommendation && (
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
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">
                    Recommendation
                  </span>
                  <Badge variant="outline" className="text-primary">
                    {claim.aiRecommendation.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">
                    AI Confidence
                  </span>
                  <span className="text-lg font-bold text-primary">
                    {claim.aiRecommendation.confidence}%
                  </span>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-muted/50 to-muted/30 p-4 border">
                  <p className="text-sm leading-relaxed text-foreground">{claim.aiRecommendation.reasoning}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Documents & Actions */}
        <div className="space-y-6">
          {/* Documents */}
          <Card className="rounded-2xl border-0 shadow-sm">
            <CardHeader className="border-b bg-muted/30 px-6 py-4">
              <CardTitle className="text-xl">Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-6">
              {claim.documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-xl border bg-card p-4 smooth-transition hover:shadow-md hover:border-primary/30"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">{doc.name}</p>
                      <p className="text-xs text-muted-foreground">{doc.size}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => handleDownload(doc.name)} className="rounded-lg hover:bg-primary/10 hover:text-primary">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Actions */}
          <Card className="rounded-2xl border-0 shadow-sm">
            <CardHeader className="border-b bg-muted/30 px-6 py-4">
              <CardTitle className="text-xl">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-6">
              {claim.status === 'pending' && (
                <Button variant="destructive" className="w-full rounded-xl shadow-sm" onClick={handleWithdraw}>
                  Withdraw Claim
                </Button>
              )}
              <Button variant="outline" className="w-full rounded-xl" onClick={() => navigate('/claims')}>
                Back to Claims
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
