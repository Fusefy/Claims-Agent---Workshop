import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Upload, X, FileText, ArrowLeft, Send, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { claimsApi } from '@/lib/api';

export default function NewClaim() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [customerId, setCustomerId] = useState('');
  const [policyId, setPolicyId] = useState('');

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(e.target.files || []);
    setFiles([...files, ...uploadedFiles]);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      toast({
        title: 'Main document required',
        description: 'Please upload your main claim document to continue.',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const mainFile = files[0];
      
      const metadata: { customer_id?: string; policy_id?: string } = {};
      if (customerId) metadata.customer_id = customerId;
      if (policyId) metadata.policy_id = policyId;

      await claimsApi.submitClaim(mainFile, metadata);

      // Show success card
      setShowSuccess(true);
      
      // Redirect after 2 seconds
      setTimeout(() => navigate('/claims'), 2000);
    } catch (error: any) {
      console.error('Claim submission error:', error);
      
      toast({
        title: 'Claim Submission Failed',
        description: 'An error occurred while processing your claim. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show success card after submission
  if (showSuccess) {
    return (
      <div className="container mx-auto max-w-2xl min-h-screen flex items-center justify-center py-8">
        <Card className="rounded-2xl border-0 shadow-lg w-full">
          <CardContent className="p-12 text-center">
            <div className="flex justify-center mb-6">
              <div className="rounded-full bg-success/10 p-6">
                <CheckCircle2 className="h-16 w-16 text-success" />
              </div>
            </div>
            <h2 className="text-3xl font-bold text-foreground mb-3">
              Your Claim Has Been Processed
            </h2>
            <p className="text-muted-foreground text-lg mb-8">
              Redirecting to your claims...
            </p>
            <div className="flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl space-y-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-bold tracking-tight text-foreground">Initiate New Claim</h1>
        <Button variant="ghost" onClick={() => navigate('/')} className="gap-2 rounded-xl hover:bg-muted">
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>

      {/* Upload Claim Document */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader className="border-b bg-muted/30 px-6 py-4">
          <CardTitle className="text-xl flex items-center gap-2">
            Upload Claim Document
            <span className="text-destructive">*</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 p-6">
          <p className="text-sm text-muted-foreground">
            Upload your receipt, invoice, or claim form (PDF or image).
          </p>

          <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-border bg-gradient-to-br from-background to-muted/20 p-16 smooth-transition hover:border-primary hover:shadow-md">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10">
              <Upload className="h-8 w-8 text-primary" />
            </div>
            <p className="mb-2 text-base font-medium text-foreground">
              Drag & drop your file here, or click to select a file.
            </p>
            <p className="mb-4 text-sm text-muted-foreground">
              (PDF, JPG, PNG supported - Max 10MB)
            </p>
            <Input
              type="file"
              onChange={(e) => handleFileUpload(e)}
              className="hidden"
              id="file-upload"
              accept=".pdf,.jpg,.jpeg,.png"
              disabled={isSubmitting}
            />
            <Button variant="outline" size="sm" asChild className="rounded-xl" disabled={isSubmitting}>
              <label htmlFor="file-upload" className="cursor-pointer">
                Choose File
              </label>
            </Button>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="mt-4 space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-xl border bg-card p-4 smooth-transition hover:shadow-md"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeFile(index)}
                    className="rounded-lg hover:bg-destructive/10 hover:text-destructive"
                    disabled={isSubmitting}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/claims')} 
              className="rounded-xl"
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={files.length === 0 || isSubmitting}
              className="gap-2 rounded-xl shadow-sm"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing Claim...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  Submit Claim
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
