import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Shield, AlertTriangle, Search, Filter, History, Target, Zap, Clock, Info, CheckCircle, BarChart3, RefreshCw } from 'lucide-react';
import Monitoring from './Monitoring';
import { RiskFeedbackForm } from '@/components/feedback/RiskFeedbackForm';
import './Validation.css';

interface FilterState {
  severity: string;
  status: string;
  component: string;
  dateRange: [string, string] | null;
  searchTerm: string;
}

interface MetricsData {
  modelInfo: {
    name: string;
    version: string;
    status?: string;
    lastUpdated?: string;
    approvedBy?: string;
    approvedDate?: string;
  };
  metrics: {
    [key: string]: number | string;
  };
  chartData: {
    metricsOverTime: Array<{
      date: string;
      [key: string]: number | string;
    }>;
    vulnerabilityTrends?: Array<{
      date: string;
      critical: number;
      high: number;
      medium: number;
      low: number;
    }>;
    threatDetection?: Array<{
      type: string;
      detected: number;
      blocked: number;
    }>;
  };
  securityThreats?: {
    promptInjection?: {
      detectedAttempts: number;
      blockedAttempts: number;
      successRate: number;
      riskLevel: string;
      commonPatterns: string[];
    };
    toolAbuse?: {
      riskLevel: string;
      detectedAttempts: number;
      blockedAttempts: number;
      successRate: number;
      commonPatterns: string[];
    };
    threats?: Array<{
      type: string;
      severity: string;
      count: number;
      blocked: number;
      date: string;
    }>;
  };
  sbom?: {
    totalComponents?: number;
    criticalVulnerabilities: number;
    highVulnerabilities: number;
    mediumVulnerabilities: number;
    lowVulnerabilities: number;
    components: any[];
  };
  cspm?: {
    overallScore: number;
    policies: Array<{
      name: string;
      status: string;
      score: number;
      issues: number;
    }>;
  };
  vulnerabilityLibrary?: Array<{
    id: string;
    severity: string;
    component: string;
    cvss: number;
    status: string;
    description: string;
    discoveredDate?: string;
  }>;
  versionHistory: Array<{
    version: string;
    date: string;
    status: string;
    changes: string;
  }>;
  agentEvaluators?: Array<{
    name: string;
    signal: string;
    definition: string;
    judging_method: string;
  }>;
}

// Default/fallback data for security sections (will be replaced by separate script)
const defaultSecurityData = {
  securityThreats: {
    promptInjection: {
      detectedAttempts: 0,
      blockedAttempts: 0,
      successRate: 100,
      riskLevel: 'low',
      commonPatterns: ['No data available - run security validation script']
    }
  },
  chartData: {
    threatDetection: [
      { type: 'No Data', detected: 0, blocked: 0 },
    ]
  },
  sbom: {
    criticalVulnerabilities: 0,
    highVulnerabilities: 0,
    mediumVulnerabilities: 0,
    lowVulnerabilities: 0,
    components: []
  },
  vulnerabilityLibrary: []
};

export default function Validation() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metricsData, setMetricsData] = useState<MetricsData | null>(null);
  const [filteredData, setFilteredData] = useState<MetricsData | null>(null);
  const [selectedChart, setSelectedChart] = useState<string>('');
  const [filters, setFilters] = useState<FilterState>({
    severity: 'all',
    status: 'all',
    component: 'all',
    dateRange: null,
    searchTerm: ''
  });

  // Helper function to convert metric names from Title Case to camelCase
  const toCamelCase = (str: string): string => {
    return str
      .split(' ')
      .map((word, index) => {
        if (index === 0) {
          return word.charAt(0).toLowerCase() + word.slice(1);
        }
        return word.charAt(0).toUpperCase() + word.slice(1);
      })
      .join('')
      .replace(/[^a-zA-Z0-9]/g, '');
  };

  // Helper function to get metric value by display name
  const getMetricValue = (data: MetricsData | null, displayName: string): number => {
    if (!data || !data.metrics) {
      return 0;
    }
    const value = data.metrics[displayName];
    return typeof value === 'number' ? value : 0;
  };

  // Fetch metrics data from API
  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/metrics/latest`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch metrics data');
      }
      
      const data = await response.json();

      // Merge with default security data (use defaults only if API data is missing)
      const mergedData = {
        ...defaultSecurityData,
        ...data,
        chartData: {
          ...defaultSecurityData.chartData,
          ...data.chartData
        }
      };

      setMetricsData(mergedData);
      setFilteredData(mergedData);
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount
  useEffect(() => {
    fetchMetrics();
  }, []);

  // Apply filters when they change
  useEffect(() => {
    if (!metricsData) return;

    const filtered = { ...metricsData };

    // Apply filters to vulnerability library if it exists
    if (filtered.vulnerabilityLibrary && (filters.severity !== 'all' || filters.status !== 'all' || filters.component !== 'all' || filters.searchTerm)) {
      filtered.vulnerabilityLibrary = metricsData.vulnerabilityLibrary!.filter((item: any) => {
        const matchesSeverity = filters.severity === 'all' || item.severity === filters.severity;
        const matchesStatus = filters.status === 'all' || item.status === filters.status;
        const matchesComponent = filters.component === 'all' || item.component === filters.component;
        const matchesSearch =
          !filters.searchTerm ||
          item.description.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
          item.id.toLowerCase().includes(filters.searchTerm.toLowerCase());

        return matchesSeverity && matchesStatus && matchesComponent && matchesSearch;
      });
    }

    setFilteredData(filtered);
  }, [filters, metricsData]);

  const handleChartClick = (chartType: string, dataPoint?: any) => {
    setSelectedChart(chartType);

    if (chartType === 'vulnerabilities' && dataPoint) {
      setFilters((prev) => ({
        ...prev,
        severity: dataPoint.name.toLowerCase()
      }));
    } else if (chartType === 'threats' && dataPoint) {
      setFilters((prev) => ({
        ...prev,
        searchTerm: dataPoint.type
      }));
    }
  };

  const resetFilters = () => {
    setFilters({
      severity: 'all',
      status: 'all',
      component: 'all',
      dateRange: null,
      searchTerm: ''
    });
    setSelectedChart('');
  };

  const getBadgeVariant = (severity: string): "default" | "destructive" | "outline" | "secondary" => {
    if (severity === 'critical') return 'destructive';
    if (severity === 'high') return 'destructive';
    if (severity === 'medium') return 'default';
    return 'secondary';
  };

  const getStatusBadgeVariant = (status: string): "default" | "destructive" | "outline" | "secondary" => {
    if (status === 'patched' || status === 'production' || status === 'approved') return 'default';
    if (status === 'open' || status === 'under_testing') return 'secondary';
    return 'outline';
  };

  const vulnerabilityChartData = [
    { name: 'Critical', value: filteredData?.sbom?.criticalVulnerabilities, color: '#f5222d' },
    { name: 'High', value: filteredData?.sbom?.highVulnerabilities, color: '#faad14' },
    { name: 'Medium', value: filteredData?.sbom?.mediumVulnerabilities, color: '#722ed1' },
    { name: 'Low', value: filteredData?.sbom?.lowVulnerabilities, color: '#52c41a' }
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        <p className="text-muted-foreground">Loading metrics data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertTriangle className="h-12 w-12 text-destructive" />
        <p className="text-destructive font-semibold">{error}</p>
        <Button onClick={fetchMetrics} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  if (!filteredData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertTriangle className="h-12 w-12 text-yellow-500" />
        <p className="text-muted-foreground">No metrics data available</p>
        <Button onClick={fetchMetrics} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Load Metrics
        </Button>
      </div>
    );
  }

  return (
    <div className="validation-container">
      <Tabs defaultValue="validation" className="w-full">
        <TabsList className="mb-6 grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="validation">AI Validation</TabsTrigger>
          <TabsTrigger value="monitoring">AI Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="validation">
          {/* Header */}
          <Card className="mb-6">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-primary">{filteredData?.modelInfo.name}</h1>
                  <p className="text-sm text-muted-foreground mt-1">{filteredData?.modelInfo.version}</p>
                </div>

              </div>
            </CardContent>
          </Card>

          {/* Agent Metrics (KPI) */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Agent Metrics (KPI)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                {/* Claims Processing Straight-Through Rate */}
                <div className="metric-card-enhanced">
                  <div className="metric-icon-wrapper" style={{ backgroundColor: '#d1f4e0' }}>
                    <Target className="metric-icon" style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-content">
                    <div className="metric-value-large" style={{ color: '#10b981' }}>
                      {getMetricValue(filteredData, 'Claims Processing Straight-Through Rate')}%
                    </div>
                    <div className="metric-label-enhanced">Claims Processing Straight-Through Rate</div>
                    <div className="metric-description">
                      Percentage of claims processed automatically without requiring manual intervention or review.
                    </div>
                  </div>
                </div>

                {/* Error Rate on Approved Claims */}
                <div className="metric-card-enhanced">
                  <div className="metric-icon-wrapper" style={{ backgroundColor: '#d1f4e0' }}>
                    <Zap className="metric-icon" style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-content">
                    <div className="metric-value-large" style={{ color: '#10b981' }}>
                      {getMetricValue(filteredData, 'Error Rate on Approved Claims')}%
                    </div>
                    <div className="metric-label-enhanced">Error Rate on Approved Claims</div>
                    <div className="metric-description">
                      Proportion of processing errors found in claims that were approved, indicating quality control effectiveness.
                    </div>
                  </div>
                </div>

                {/* Time to Adjudication Reduction */}
                <div className="metric-card-enhanced">
                  <div className="metric-icon-wrapper" style={{ backgroundColor: '#d1f4e0' }}>
                    <Clock className="metric-icon" style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-content">
                    <div className="metric-value-large" style={{ color: '#10b981' }}>
                      {getMetricValue(filteredData, 'Time to Adjudication Reduction')}s
                    </div>
                    <div className="metric-label-enhanced">Time to Adjudication Reduction</div>
                    <div className="metric-description">
                      Percentage improvement in claim adjudication speed compared to manual processing baseline.
                    </div>
                  </div>
                </div>

                {/* Claim Denial Rate */}
                <div className="metric-card-enhanced">
                  <div className="metric-icon-wrapper" style={{ backgroundColor: '#d1f4e0' }}>
                    <TrendingUp className="metric-icon" style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-content">
                    <div className="metric-value-large" style={{ color: '#10b981' }}>
                      {getMetricValue(filteredData, 'Claim Denial Rate')}%
                    </div>
                    <div className="metric-label-enhanced">Claim Denial Rate</div>
                    <div className="metric-description">
                      Proportion of claims denied by the system, reflecting accuracy in policy validation and fraud detection.
                    </div>
                  </div>
                </div>

                {/* Compliance Dashboard Accuracy */}
                <div className="metric-card-enhanced">
                  <div className="metric-icon-wrapper" style={{ backgroundColor: '#d1f4e0' }}>
                    <Info className="metric-icon" style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-content">
                    <div className="metric-value-large" style={{ color: '#10b981' }}>
                      {getMetricValue(filteredData, 'Compliance Dashboard Accuracy')}%
                    </div>
                    <div className="metric-label-enhanced">Compliance Dashboard Accuracy</div>
                    <div className="metric-description">
                      Accuracy of compliance reporting dashboards in correctly reflecting processed claims data and regulatory status.
                    </div>
                  </div>
                </div>

                {/* Integration Accuracy */}
                <div className="metric-card-enhanced">
                  <div className="metric-icon-wrapper" style={{ backgroundColor: '#d1f4e0' }}>
                    <CheckCircle className="metric-icon" style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-content">
                    <div className="metric-value-large" style={{ color: '#10b981' }}>
                      {getMetricValue(filteredData, 'Integration Accuracy')}%
                    </div>
                    <div className="metric-label-enhanced">Integration Accuracy</div>
                    <div className="metric-description">
                      Correctness of data synchronization and integration with existing insurance management systems.
                    </div>
                  </div>
                </div>

                {/* Processing Latency */}
                <div className="metric-card-enhanced">
                  <div className="metric-icon-wrapper" style={{ backgroundColor: '#d1f4e0' }}>
                    <BarChart3 className="metric-icon" style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-content">
                    <div className="metric-value-large" style={{ color: '#10b981' }}>
                      {getMetricValue(filteredData, 'Processing Latency')}s
                    </div>
                    <div className="metric-label-enhanced">Processing Latency</div>
                    <div className="metric-description">
                      Average time in seconds required to process a claim from intake to decision.
                    </div>
                  </div>
                </div>
              </div>

              {/* Percentage Metrics Chart */}
              <div className="h-80 mb-6">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={filteredData?.chartData?.metricsOverTime}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      label={{ value: 'Date', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
                      domain={[0, 100]}
                    />
                    <Tooltip />
                    <Legend
                      wrapperStyle={{ paddingTop: '10px' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Claims Processing Straight-Through Rate"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      name="Claims Processing Rate"
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Error Rate on Approved Claims"
                      stroke="#ef4444"
                      strokeWidth={2}
                      name="Error Rate"
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Compliance Dashboard Accuracy"
                      stroke="#10b981"
                      strokeWidth={2}
                      name="Compliance Accuracy"
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Integration Accuracy"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      name="Integration Accuracy"
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <p className="text-center text-sm text-muted-foreground mt-2">Percentage Metrics Over Time</p>
              </div>

              {/* Seconds Metrics Chart */}
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={filteredData?.chartData?.metricsOverTime}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      label={{ value: 'Date', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      label={{ value: 'Time (Seconds)', angle: -90, position: 'insideLeft' }}
                      domain={[0, 'auto']}
                    />
                    <Tooltip />
                    <Legend
                      wrapperStyle={{ paddingTop: '10px' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Processing Latency"
                      stroke="#f97316"
                      strokeWidth={2}
                      name="Processing Latency"
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Time to Adjudication Reduction"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      name="Adjudication Time Reduction"
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <p className="text-center text-sm text-muted-foreground mt-2">Time-based Metrics (Seconds) Over Time</p>
              </div>
            </CardContent>
          </Card>

          {/* Security Threats Analysis (KRI) */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Security Threats Analysis (KRI)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg">Prompt Injection Detection</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="threat-stat">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                        <span className="text-2xl font-bold">{filteredData?.securityThreats?.promptInjection?.detectedAttempts}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">Detected</p>
                    </div>
                    <div className="threat-stat">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <Shield className="h-4 w-4 text-green-500" />
                        <span className="text-2xl font-bold">{filteredData?.securityThreats?.promptInjection?.blockedAttempts}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">Blocked</p>
                    </div>
                    <div className="threat-stat">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <TrendingUp className="h-4 w-4 text-blue-500" />
                        <span className="text-xl font-bold">{filteredData?.securityThreats?.promptInjection?.successRate}%</span>
                      </div>
                      <p className="text-sm text-muted-foreground">Success Rate</p>
                    </div>
                    <div className="threat-stat">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                        <span className="text-xl font-bold">{filteredData?.securityThreats?.promptInjection?.riskLevel.toUpperCase()}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">Risk Level</p>
                    </div>
                  </div>
                  <div className="patterns-box">
                    <p className="font-semibold text-sm mb-2">Common Attack Patterns</p>
                    <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                      {filteredData?.securityThreats?.promptInjection?.commonPatterns.map(
                        (pattern: string, index: number) => <li key={index}>{pattern}</li>
                      )}
                    </ul>
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-4">Threat Detection Summary</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={filteredData?.chartData?.threatDetection}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="type" angle={-15} textAnchor="end" height={80} />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="detected" fill="#f59e0b" />
                        <Bar dataKey="blocked" fill="#10b981" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Filters & Search */}
          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Filters & Search
                </CardTitle>
                <Button variant="link" onClick={resetFilters}>
                  Reset All Filters
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Select value={filters.severity} onValueChange={(value) => setFilters((prev) => ({ ...prev, severity: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Severities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Severities</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filters.status} onValueChange={(value) => setFilters((prev) => ({ ...prev, status: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="patched">Patched</SelectItem>
                    <SelectItem value="validated">Validated</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filters.component} onValueChange={(value) => setFilters((prev) => ({ ...prev, component: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Components" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Components</SelectItem>
                    <SelectItem value="pandas">Pandas</SelectItem>
                    <SelectItem value="numpy">NumPy</SelectItem>
                  </SelectContent>
                </Select>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search..."
                    value={filters.searchTerm}
                    onChange={(e) => setFilters((prev) => ({ ...prev, searchTerm: e.target.value }))}
                    className="pl-9"
                  />
                </div>
              </div>
              {selectedChart && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <strong>Active Filter:</strong> Chart selection - {selectedChart}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Vulnerability Overview */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Vulnerability Overview (KRI)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={vulnerabilityChartData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        onClick={(data) => handleChartClick('vulnerabilities', data)}
                        label
                      >
                        {vulnerabilityChartData?.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="vuln-stat critical">
                    <div className="vuln-number">{filteredData?.sbom?.criticalVulnerabilities}</div>
                    <div className="vuln-label">Critical</div>
                  </div>
                  <div className="vuln-stat high">
                    <div className="vuln-number">{filteredData?.sbom?.highVulnerabilities}</div>
                    <div className="vuln-label">High</div>
                  </div>
                  <div className="vuln-stat medium">
                    <div className="vuln-number">{filteredData?.sbom?.mediumVulnerabilities}</div>
                    <div className="vuln-label">Medium</div>
                  </div>
                  <div className="vuln-stat low">
                    <div className="vuln-number">{filteredData?.sbom?.lowVulnerabilities}</div>
                    <div className="vuln-label">Low</div>
                  </div>
                </div>
              </div>

              <Tabs defaultValue="library" className="w-full">
                <TabsList>
                  <TabsTrigger value="library">
                    <Shield className="h-4 w-4 mr-2" />
                    Vulnerability Library
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="library">
                  {filteredData?.vulnerabilityLibrary && filteredData.vulnerabilityLibrary.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>CVE ID</TableHead>
                          <TableHead>Severity</TableHead>
                          <TableHead>Component</TableHead>
                          <TableHead>CVSS Score</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Description</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredData.vulnerabilityLibrary.map((vuln: any) => (
                          <TableRow key={vuln.id}>
                            <TableCell className="font-mono text-blue-600">{vuln.id}</TableCell>
                            <TableCell>
                              <Badge variant={getBadgeVariant(vuln.severity)}>
                                {vuln.severity.toUpperCase()}
                              </Badge>
                            </TableCell>
                            <TableCell>{vuln.component}</TableCell>
                            <TableCell className="font-semibold">{vuln.cvss}</TableCell>
                            <TableCell>
                              <Badge variant={getStatusBadgeVariant(vuln.status)}>
                                {vuln.status.toUpperCase()}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-md truncate">{vuln.description}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <Shield className="h-12 w-12 text-muted-foreground mb-4" />
                      <p className="text-muted-foreground font-semibold">No vulnerability data available</p>
                      <p className="text-sm text-muted-foreground mt-2">Run the security validation script to populate this section</p>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Version History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Version History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {filteredData?.versionHistory?.map((version: any, index: number) => (
                  <div key={index} className="version-item">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-lg font-bold text-primary">{version.version}</span>
                      <span className="text-sm text-muted-foreground">{new Date(version.date).toLocaleDateString()}</span>
                      <Badge variant={getStatusBadgeVariant(version.status)}>
                        {version.status.replace('_', ' ').toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{version.changes}</p>
                    {index < filteredData.versionHistory.length - 1 && <div className="border-b mt-4" />}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring">
          <Monitoring />
        </TabsContent>

      </Tabs>

      {/* Risk Feedback Floating Action Button */}
      <RiskFeedbackForm />
    </div >
  );
}
