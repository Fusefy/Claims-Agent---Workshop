// src/lib/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// TypeScript interfaces
export interface User {
  user_id: number;
  username: string;
  email: string;
  google_id?: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface ProposedClaim {
  claim_id: string;
  claim_name?: string;  // NEW: Short descriptive name for the claim
  customer_id: string;
  policy_id?: string;
  claim_type?: string;
  network_status?: string;
  date_of_service?: string;
  claim_amount?: number;
  approved_amount: number;
  claim_status: string;
  error_type?: string;
  ai_reasoning?: string;  // NEW: AI explanation for Approved/Pending/Denied status
  payment_status: string;
  guardrail_summary?: any;  // Updated: Now contains structured fraud detection data (JSONB)
  created_at: string;
  updated_at: string;
  // REMOVED: pre_auth_required, pre_auth_status, denial_reason, notes, 
  // last_agent, last_guardrail_status, last_guardrail_reason
}

export interface ClaimHistory {
  history_id: number;
  claim_id: string;
  old_status: string;
  new_status: string;
  changed_by: string;
  role: string;
  change_reason?: string;
  timestamp: string;
}

export interface HITLQueue {
  queue_id: number;
  claim_id: string;
  assigned_to?: number;
  status: string;
  reviewer_comments?: string;
  decision?: string;
  created_at: string;
  reviewed_at?: string;
}

export interface ClaimStatistics {
  total: number;
  approved: number;
  pending: number;
  denied: number;
  withdrawn: number;
}

export interface ClaimSubmissionResponse {
  success: boolean;
  message: string;
  claim_id?: string;
  fraud_status?: string;
  confidence?: number;
  fraud_reason?: string;
  hitl_flag?: boolean;
  gcs_path?: string;
  claim_status?: string;
  claim_amount?: number;
  error?: string;
  error_type?: string;
}

export interface ChatMessage {
  message: string;
  session_id?: string;
  context?: {
    user_id?: string;
    recent_claims_count?: number;
    pending_claims_count?: number;
  };
}

export interface ChatResponse {
  success: boolean;
  response: string;
  session_id: string;
  error?: string;
}

// Auth API
export const authApi = {
  getGoogleLoginUrl: async () => {
    const response = await api.get('/auth/google/login');
    return response.data;
  },
  
  verifyToken: async (token: string) => {
    const response = await api.post('/auth/verify', { token });
    return response.data;
  },
  
  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
};

// User API
export const userApi = {
  getUserById: async (userId: number): Promise<User> => {
    const response = await api.get(`/api/users/${userId}`);
    return response.data;
  },
  
  getUserByUsername: async (username: string): Promise<User> => {
    const response = await api.get(`/api/users/username/${username}`);
    return response.data;
  },
  
  getAllUsers: async (): Promise<User[]> => {
    const response = await api.get('/api/users/');
    return response.data;
  },
  
  getUsersByRole: async (role: string): Promise<User[]> => {
    const response = await api.get(`/api/users/role/${role}`);
    return response.data;
  },
};

// Claims API
export const claimsApiNew = {
  getClaimById: async (claimId: string): Promise<ProposedClaim> => {
    const response = await api.get(`/api/claims/${claimId}`);
    return response.data;
  },
  
  getAllClaims: async (params?: { limit?: number; offset?: number }): Promise<ProposedClaim[]> => {
    const response = await api.get('/api/claims/', { params });
    return response.data.claims || [];
  },
  
  getClaimsByCustomer: async (customerId: string, params?: { limit?: number; offset?: number }): Promise<ProposedClaim[]> => {
    const response = await api.get(`/api/claims/customer/${customerId}`, { params });
    return response.data.claims || [];
  },
  
  getClaimsByStatus: async (status: string): Promise<ProposedClaim[]> => {
    const response = await api.get(`/api/claims/status/${status}`);
    return response.data.claims || [];
  },
  
  updateClaimStatus: async (claimId: string, newStatus: string, reason?: string) => {
    const response = await api.put(`/api/claims/${claimId}/status`, {
      new_status: newStatus,
      change_reason: reason,
    });
    return response.data;
  },
  
  getClaimHistory: async (claimId: string): Promise<ClaimHistory[]> => {
    const response = await api.get(`/api/claims/${claimId}/history`);
    return response.data;
  },
  
  getClaimStatistics: async (): Promise<ClaimStatistics> => {
    const response = await api.get('/api/claims/statistics/overview');
    return response.data;
  },
  
  searchClaims: async (filters: any): Promise<ProposedClaim[]> => {
    const response = await api.post('/api/claims/search', filters);
    return response.data;
  },
};

// HITL API
export const hitlApi = {
  getQueue: async (): Promise<HITLQueue[]> => {
    const response = await api.get('/api/hitl/queue');
    return response.data;
  },
  
  getQueueItem: async (queueId: number): Promise<HITLQueue> => {
    const response = await api.get(`/api/hitl/${queueId}`);
    return response.data;
  },
  
  submitReview: async (queueId: number, decision: string, comments?: string) => {
    const response = await api.post(`/api/hitl/${queueId}/review`, {
      decision,
      reviewer_comments: comments,
    });
    return response.data;
  },
};

export const claimsApi = {
  /**
   * Submit a new claim for processing
   */
  submitClaim: async (
    file: File,
    metadata?: { customer_id?: string; policy_id?: string }
  ): Promise<ClaimSubmissionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata?.customer_id) {
      formData.append('customer_id', metadata.customer_id);
    }
    if (metadata?.policy_id) {
      formData.append('policy_id', metadata.policy_id);
    }

    const response = await fetch(`${API_BASE_URL}/api/claims/process`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit claim');
    }

    const data = await response.json();
    
    // Backend returns: { "response": "message..." }
    // Transform it to match ClaimSubmissionResponse interface
    return {
      success: true,  // If we got here, it was successful
      message: data.response || "Claim submitted successfully",
    };
  },

  /**
   * Submit multiple claims in batch (max 10)
   */
  submitClaimsBatch: async (files: File[]): Promise<any> => {
    if (files.length > 10) {
      throw new Error('Maximum 10 files can be processed at once');
    }

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(`${API_BASE_URL}/api/claims/process/batch`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit claims batch');
    }

    return response.json();
  },

  /**
   * Get claim status by ID
   */
  getClaimStatus: async (claimId: string): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/claims/${claimId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch claim status');
    }

    return response.json();
  },

  /**
   * Get HITL queue
   */
  getHITLQueue: async (): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/claims/hitl/queue`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch HITL queue');
    }

    return response.json();
  },
};

// Utility functions
export const getStatusBadgeVariant = (status: string) => {
  const normalizedStatus = status.toLowerCase();
  if (normalizedStatus.includes('approved')) return 'success';
  if (normalizedStatus.includes('pending')) return 'warning';
  if (normalizedStatus.includes('denied') || normalizedStatus.includes('rejected')) return 'destructive';
  if (normalizedStatus.includes('withdrawn')) return 'outline';
  return 'default';
};

export const formatCurrency = (amount: number, currency: string = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
  }).format(amount);
};

export const formatDate = (dateString: string, format: 'short' | 'long' = 'short') => {
  const date = new Date(dateString);
  if (format === 'long') {
    return date.toLocaleDateString('en-US', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }
  return date.toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};

// Chat API
export const chatApi = {
  /**
   * Send a message to the AI chat assistant
   */
  sendMessage: async (message: string, sessionId?: string, context?: any): Promise<ChatResponse> => {
    const payload: ChatMessage = {
      message,
      session_id: sessionId,
      context,
    };

    const response = await api.post('/api/chat', payload);
    return response.data;
  },

  /**
   * Clear a specific chat session
   */
  clearSession: async (sessionId: string) => {
    const response = await api.delete(`/api/chat/session/${sessionId}`);
    return response.data;
  },

  /**
   * Health check for chat service
   */
  healthCheck: async () => {
    const response = await api.get('/api/chat/health');
    return response.data;
  },
};
