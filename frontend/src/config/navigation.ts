/** Sidebar navigation model — mirrors the reference dashboard's left rail. */
import {
  BadgeCheck,
  BookMarked,
  BookOpen,
  Bot,
  Brain,
  Clapperboard,
  Compass,
  Code2,
  CreditCard,
  Crown,
  FilePlus2,
  FileText,
  FolderGit2,
  LayoutDashboard,
  LayoutGrid,
  ListChecks,
  Megaphone,
  Plug,
  ScrollText,
  Settings,
  ShieldCheck,
  Cpu,
  Workflow,
} from 'lucide-react'
import type { NavGroup } from '@/types'

export const navGroups: NavGroup[] = [
  {
    label: null,
    items: [
      { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
      { label: 'Workspace', to: '/workspace', icon: LayoutGrid },
      { label: 'Projects', to: '/projects', icon: FolderGit2 },
      { label: 'Tasks', to: '/tasks', icon: ListChecks },
      { label: 'Social Studio', to: '/social', icon: Clapperboard, accent: 'violet' },
      { label: 'Document Studio', to: '/document-studio', icon: FilePlus2, accent: 'blue' },
      { label: 'Agents', to: '/agents', icon: Bot },
      { label: 'Workflows', to: '/workflows', icon: Workflow },
      { label: 'Approvals', to: '/approvals', icon: BadgeCheck, accent: 'amber' },
      { label: 'Documents', to: '/documents', icon: FileText },
      { label: 'Knowledge Base', to: '/knowledge', icon: BookOpen },
    ],
  },
  {
    label: 'Departments',
    items: [
      { label: 'Executive', to: '/departments/executive', icon: Crown, accent: 'cyan' },
      { label: 'Architecture', to: '/departments/architecture', icon: Compass, accent: 'violet' },
      { label: 'Engineering', to: '/departments/engineering', icon: Code2, accent: 'blue' },
      { label: 'Quality & Security', to: '/departments/quality', icon: ShieldCheck, accent: 'emerald' },
      { label: 'Marketing', to: '/departments/marketing', icon: Megaphone, accent: 'amber' },
      { label: 'Documentation', to: '/departments/documentation', icon: BookMarked, accent: 'violet' },
      { label: 'System Operations', to: '/departments/system-ops', icon: Cpu, accent: 'cyan' },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'Memory', to: '/memory', icon: Brain },
      { label: 'Logs', to: '/logs', icon: ScrollText },
      { label: 'Settings', to: '/settings', icon: Settings },
      { label: 'Integrations', to: '/integrations', icon: Plug },
      { label: 'Billing', to: '/billing', icon: CreditCard },
    ],
  },
]
