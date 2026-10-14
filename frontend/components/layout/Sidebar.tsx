'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  BookOpen,
  CalendarDays,
  FlaskConical,
  BarChart3,
  Target,
  MessageSquare,
  Settings,
  ChevronLeft,
  ChevronRight,
  Flame,
  Brain,
  X,
  Menu,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

const navItems: NavItem[] = [
  { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { label: 'My Syllabus', href: '/syllabus', icon: BookOpen },
  { label: 'AI Study Planner', href: '/planner', icon: CalendarDays },
  { label: 'Diagnostic Tests', href: '/diagnostic', icon: FlaskConical },
  { label: 'My Progress', href: '/progress', icon: BarChart3 },
  { label: 'Exam Readiness', href: '/readiness', icon: Target },
  { label: 'AI Study Coach', href: '/coach', icon: MessageSquare },
  { label: 'Settings', href: '/settings', icon: Settings },
];

interface SidebarProps {
  studentName?: string;
  streak?: number;
}

export default function Sidebar({ studentName = 'Student', streak = 0 }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo / Brand */}
      <div
        className={cn(
          'flex items-center gap-3 px-4 py-5 border-b border-border',
          collapsed && 'justify-center px-2'
        )}
      >
        <div className="flex-shrink-0 w-9 h-9 rounded-xl gradient-violet flex items-center justify-center shadow-violet">
          <Brain className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-sm font-bold text-white leading-tight whitespace-nowrap text-gradient-violet">
              ExamWise AI
            </h1>
            <p className="text-[10px] text-muted-foreground whitespace-nowrap">
              Smart Exam Preparation
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href !== '/dashboard' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group relative',
                isActive
                  ? 'bg-violet-600/20 text-violet-300 border-l-2 border-violet-500 pl-[10px]'
                  : 'text-muted-foreground hover:text-foreground hover:bg-white/5',
                collapsed && 'justify-center px-2'
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  'flex-shrink-0 w-4.5 h-4.5 transition-colors',
                  isActive ? 'text-violet-400' : 'text-muted-foreground group-hover:text-foreground'
                )}
                size={18}
              />
              {!collapsed && (
                <span className="truncate">{item.label}</span>
              )}
              {!collapsed && item.badge && (
                <Badge
                  variant="secondary"
                  className="ml-auto text-[10px] px-1.5 py-0 bg-violet-600/30 text-violet-300 border-violet-500/30"
                >
                  {item.badge}
                </Badge>
              )}
              {/* Tooltip for collapsed state */}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-card border border-border rounded-md text-xs text-foreground whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none z-50 transition-opacity">
                  {item.label}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Student profile section */}
      <div className={cn('border-t border-border p-3', collapsed && 'px-2')}>
        <div
          className={cn(
            'flex items-center gap-3 p-2 rounded-lg bg-white/5',
            collapsed && 'justify-center'
          )}
        >
          <div className="w-8 h-8 rounded-full gradient-violet flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">
            {studentName.charAt(0).toUpperCase()}
          </div>
          {!collapsed && (
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium text-foreground truncate">
                {studentName}
              </p>
              <div className="flex items-center gap-1 mt-0.5">
                <Flame className="w-3 h-3 text-orange-400" />
                <span className="text-xs text-muted-foreground">
                  {streak} day streak
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Collapse button (desktop) */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className={cn(
          'hidden md:flex items-center justify-center h-8 border-t border-border bg-card/50 hover:bg-white/5 transition-colors text-muted-foreground hover:text-foreground',
        )}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4" />
        ) : (
          <ChevronLeft className="w-4 h-4" />
        )}
      </button>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'hidden md:flex flex-col fixed left-0 top-0 bottom-0 z-40 bg-card border-r border-border sidebar-transition',
          collapsed ? 'w-[var(--sidebar-width-collapsed)]' : 'w-[var(--sidebar-width)]'
        )}
      >
        <SidebarContent />
      </aside>

      {/* Mobile trigger */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground"
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile drawer overlay */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={cn(
          'md:hidden fixed top-0 left-0 bottom-0 z-50 w-[var(--sidebar-width)] bg-card border-r border-border flex flex-col transition-transform duration-300',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <button
          className="absolute top-4 right-4 p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation"
        >
          <X className="w-4 h-4" />
        </button>
        <SidebarContent />
      </aside>
    </>
  );
}
