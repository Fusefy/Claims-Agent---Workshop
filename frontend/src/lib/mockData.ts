export interface Claim {
  id: string;
  claimName: string;
  amount: number;
  date: string;
  status: 'approved' | 'pending' | 'denied' | 'withdrawn';
  category: string;
  description: string;
  documents: Document[];
  timeline: TimelineEvent[];
  aiRecommendation?: {
    status: string;
    confidence: number;
    reasoning: string;
  };
}

export interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadedAt: string;
  url: string;
}

export interface TimelineEvent {
  id: string;
  status: string;
  date: string;
  description: string;
}

export const mockClaims: Claim[] = [
  {
    id: '1',
    claimName: 'Medical Reimbursement - Hospital Visit',
    amount: 5420,
    date: '2025-01-15',
    status: 'approved',
    category: 'Medical',
    description: 'Emergency room visit and subsequent treatment for acute condition',
    documents: [
      { id: 'd1', name: 'Hospital_Invoice.pdf', type: 'application/pdf', size: '2.4 MB', uploadedAt: '2025-01-15', url: '#' },
      { id: 'd2', name: 'Prescription.pdf', type: 'application/pdf', size: '450 KB', uploadedAt: '2025-01-15', url: '#' },
    ],
    timeline: [
      { id: 't1', status: 'Submitted', date: '2025-01-15', description: 'Claim submitted successfully' },
      { id: 't2', status: 'Under Review', date: '2025-01-16', description: 'Documents verified by claims team' },
      { id: 't3', status: 'Approved', date: '2025-01-18', description: 'Claim approved for reimbursement' },
    ],
    aiRecommendation: {
      status: 'Approved',
      confidence: 95,
      reasoning: 'All required documents present. Medical necessity confirmed. Within policy limits.',
    },
  },
  {
    id: '2',
    claimName: 'Travel Reimbursement - Business Trip',
    amount: 3250,
    date: '2025-01-10',
    status: 'pending',
    category: 'Travel',
    description: 'Client meeting in Mumbai - flight and accommodation expenses',
    documents: [
      { id: 'd3', name: 'Flight_Ticket.pdf', type: 'application/pdf', size: '1.1 MB', uploadedAt: '2025-01-10', url: '#' },
      { id: 'd4', name: 'Hotel_Receipt.pdf', type: 'application/pdf', size: '890 KB', uploadedAt: '2025-01-10', url: '#' },
    ],
    timeline: [
      { id: 't4', status: 'Submitted', date: '2025-01-10', description: 'Claim submitted successfully' },
      { id: 't5', status: 'Under Review', date: '2025-01-11', description: 'Awaiting manager approval' },
    ],
    aiRecommendation: {
      status: 'Likely Approved',
      confidence: 88,
      reasoning: 'Expenses align with company travel policy. Awaiting final manager sign-off.',
    },
  },
  {
    id: '3',
    claimName: 'Equipment Reimbursement - Laptop',
    amount: 8900,
    date: '2025-01-05',
    status: 'denied',
    category: 'Equipment',
    description: 'Personal laptop purchase for work purposes',
    documents: [
      { id: 'd5', name: 'Purchase_Invoice.pdf', type: 'application/pdf', size: '1.5 MB', uploadedAt: '2025-01-05', url: '#' },
    ],
    timeline: [
      { id: 't6', status: 'Submitted', date: '2025-01-05', description: 'Claim submitted successfully' },
      { id: 't7', status: 'Under Review', date: '2025-01-06', description: 'Documents reviewed' },
      { id: 't8', status: 'Denied', date: '2025-01-08', description: 'Exceeds equipment policy limits' },
    ],
    aiRecommendation: {
      status: 'Denied',
      confidence: 92,
      reasoning: 'Purchase exceeds maximum equipment reimbursement limit of $50,000 without pre-approval.',
    },
  },
  {
    id: '4',
    claimName: 'Medical Reimbursement - Pharmacy',
    amount: 1150,
    date: '2025-01-20',
    status: 'approved',
    category: 'Medical',
    description: 'Prescription medications and medical supplies',
    documents: [
      { id: 'd6', name: 'Pharmacy_Bill.pdf', type: 'application/pdf', size: '680 KB', uploadedAt: '2025-01-20', url: '#' },
    ],
    timeline: [
      { id: 't9', status: 'Submitted', date: '2025-01-20', description: 'Claim submitted successfully' },
      { id: 't10', status: 'Approved', date: '2025-01-21', description: 'Fast-tracked approval for routine medical expenses' },
    ],
    aiRecommendation: {
      status: 'Approved',
      confidence: 98,
      reasoning: 'Standard pharmacy claim with valid prescription. All documentation in order.',
    },
  },
  {
    id: '5',
    claimName: 'Meal Reimbursement - Client Dinner',
    amount: 2840,
    date: '2025-01-12',
    status: 'pending',
    category: 'Entertainment',
    description: 'Business dinner with prospective client',
    documents: [
      { id: 'd7', name: 'Restaurant_Bill.pdf', type: 'application/pdf', size: '520 KB', uploadedAt: '2025-01-12', url: '#' },
    ],
    timeline: [
      { id: 't11', status: 'Submitted', date: '2025-01-12', description: 'Claim submitted successfully' },
      { id: 't12', status: 'Under Review', date: '2025-01-13', description: 'Verifying attendee details' },
    ],
  },
];

export const claimStats = {
  total: 28,
  approved: 18,
  pending: 6,
  denied: 3,
  withdrawn: 1,
};
