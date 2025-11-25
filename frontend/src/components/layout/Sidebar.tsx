import { useState, useEffect } from 'react';
import { LayoutDashboard, FileText, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import { NavLink } from '@/components/NavLink';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';

interface SidebarProps {
  onCollapsedChange?: (collapsed: boolean) => void;
}

export function Sidebar({ onCollapsedChange }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(() => {
    // Load from localStorage or default to false
    const stored = localStorage.getItem('sidebar-collapsed');
    return stored ? JSON.parse(stored) : false;
  });

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: FileText, label: 'My Claims', path: '/claims' },
    { icon: Settings, label: 'Settings', path: '/profile' },
  ];

  useEffect(() => {
    // Persist to localStorage
    localStorage.setItem('sidebar-collapsed', JSON.stringify(isCollapsed));
    // Notify parent component
    onCollapsedChange?.(isCollapsed);
  }, [isCollapsed, onCollapsedChange]);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className="relative">
      <aside
        className={cn(
          'fixed left-0 top-16 z-30 h-[calc(100vh-4rem)] border-r bg-card/80 backdrop-blur-sm transition-all duration-300 ease-in-out',
          isCollapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Navigation */}
        <nav className="flex flex-col gap-1 p-2">
          {navItems.map((item) => {
            const navLink = (
              <NavLink
                key={item.path}
                to={item.path}
                end
                className={cn(
                  'flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-muted-foreground transition-all duration-200 hover:bg-primary/10 hover:text-foreground',
                  isCollapsed && 'justify-center px-0'
                )}
                activeClassName="bg-primary/10 text-primary shadow-sm hover:bg-primary/15 hover:text-primary"
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                <span
                  className={cn(
                    'transition-all duration-300',
                    isCollapsed ? 'w-0 opacity-0 overflow-hidden' : 'w-auto opacity-100'
                  )}
                >
                  {item.label}
                </span>
              </NavLink>
            );

            // Wrap in tooltip when collapsed
            if (isCollapsed) {
              return (
                <Tooltip key={item.path} delayDuration={0}>
                  <TooltipTrigger asChild>
                    {navLink}
                  </TooltipTrigger>
                  <TooltipContent side="right" className="font-medium">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              );
            }

            return navLink;
          })}
        </nav>
      </aside>

      {/* Toggle Button - Centered on sidebar right edge */}
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleSidebar}
        className={cn(
          'fixed top-1/2 z-40 h-8 w-8 -translate-y-1/2 rounded-r-lg transition-all duration-300 hover:bg-primary/10 active:scale-95',
          isCollapsed ? 'left-16' : 'left-64'
        )}
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4 transition-transform duration-300" />
        ) : (
          <ChevronLeft className="h-4 w-4 transition-transform duration-300" />
        )}
      </Button>
    </div>
  );
}
