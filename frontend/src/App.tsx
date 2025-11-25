import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { AIAssistantPanel } from "@/components/AIAssistantPanel";
import { ThemeProvider } from "@/hooks/useTheme";
import { UserProvider, useUser } from "@/contexts/UserContext";
import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Claims from "./pages/Claims";
import NewClaim from "./pages/NewClaim";
import ClaimDetails from "./pages/ClaimDetails";
import Profile from "./pages/Profile";
import Validation from "./pages/Validation";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";

const queryClient = new QueryClient();

function AppContent() {
  const { user, logout, loading } = useUser();
  const [isAIChatOpen, setIsAIChatOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    const stored = localStorage.getItem('sidebar-collapsed');
    return stored ? JSON.parse(stored) : false;
  });

  const isAuthenticated = !!user;

  // Protected Route wrapper
  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (loading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </div>
      );
    }
    
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
  };

  // Layout wrapper for authenticated pages
  const AuthenticatedLayout = ({ children }: { children: React.ReactNode }) => (
    <>
      <Navbar onOpenAIChat={() => setIsAIChatOpen(true)} onLogout={logout} />
      <div className="flex">
        <Sidebar onCollapsedChange={setIsSidebarCollapsed} />
        <main 
          className={`flex-1 p-6 pt-6 transition-all duration-300 ease-in-out ${
            isSidebarCollapsed ? 'ml-16' : 'ml-64'
          }`}
        >
          {children}
        </main>
      </div>
      <AIAssistantPanel
        isOpen={isAIChatOpen}
        onClose={() => setIsAIChatOpen(false)}
      />
    </>
  );

  return (
    <BrowserRouter>
      <div className="min-h-screen w-full bg-background transition-colors duration-300">
        <Routes>
          <Route 
            path="/login" 
            element={
              isAuthenticated ? <Navigate to="/" replace /> : <Login onLogin={() => {}} />
            } 
          />
          <Route 
            path="/auth/callback" 
            element={<AuthCallback />} 
          />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Dashboard />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/claims"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Claims />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/claims/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <NewClaim />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/claims/:id"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <ClaimDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Profile onLogout={logout} />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/validation"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Validation />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <UserProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <AppContent />
          </TooltipProvider>
        </UserProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
