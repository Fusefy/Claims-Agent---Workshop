import { Bot, User, ShieldCheck, LogOut, UserCircle, Sun, Moon, Monitor } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import shieldLogo from '@/assets/shield-check-logo.svg';
import { useTheme } from '@/hooks/useTheme';
import { useUser } from '@/contexts/UserContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from '@/components/ui/dropdown-menu';

interface NavbarProps {
  onOpenAIChat: () => void;
  onLogout: () => void;
}

export function Navbar({ onOpenAIChat, onLogout }: NavbarProps) {
  const navigate = useNavigate();
  const { theme, setTheme, actualTheme } = useTheme();
  const { user } = useUser();

  const themeOptions = [
    { value: 'light' as const, label: 'Light', icon: Sun },
    { value: 'dark' as const, label: 'Dark', icon: Moon },
    { value: 'system' as const, label: 'System', icon: Monitor },
  ];

  // Format employee ID from user_id
  const employeeId = user ? `EMP-2024-${user.user_id.toString().padStart(4, '0')}` : '';

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur-md shadow-sm theme-transition">
      <div className="container flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary p-1.5 theme-transition">
            <img src={shieldLogo} alt="Claims Agent Logo" className="h-full w-full" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">Claims Agent</h1>
            <p className="text-xs font-medium text-muted-foreground">Reimbursement Management</p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/validation')}
            className="relative rounded-xl hover:bg-primary/10 hover:text-primary smooth-transition"
          >
            <ShieldCheck className="h-5 w-5" />
            <span className="sr-only">Validation</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onOpenAIChat}
            className="relative rounded-xl hover:bg-primary/10 hover:text-primary smooth-transition"
          >
            <Bot className="h-5 w-5" />
            <span className="sr-only">AI Assistant</span>
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-xl hover:bg-primary/10 hover:text-primary smooth-transition"
              >
                <User className="h-5 w-5" />
                <span className="sr-only">Profile</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-background">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user?.username || 'User'}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email || 'No email'}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {employeeId}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/profile')} className="cursor-pointer">
                <UserCircle className="mr-2 h-4 w-4" />
                <span>Profile Settings</span>
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger className="cursor-pointer">
                  {actualTheme === 'dark' ? (
                    <Moon className="mr-2 h-4 w-4" />
                  ) : (
                    <Sun className="mr-2 h-4 w-4" />
                  )}
                  <span>Theme</span>
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent className="bg-background">
                  {themeOptions.map((option) => (
                    <DropdownMenuItem
                      key={option.value}
                      onClick={() => setTheme(option.value)}
                      className="cursor-pointer"
                    >
                      <option.icon className="mr-2 h-4 w-4" />
                      <span>{option.label}</span>
                      {theme === option.value && (
                        <span className="ml-auto text-primary">✓</span>
                      )}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={() => {
                  onLogout();
                  navigate('/login');
                }} 
                className="cursor-pointer text-red-600 focus:text-red-600"
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Logout</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
