/**
 * Icon registry — resolves the string `icon` keys carried by API DTOs into Lucide
 * components. The backend seed (backend/app/data/seed.py) only emits keys present here.
 */
import {
  Activity,
  Bot,
  CheckCircle2,
  Circle,
  Code2,
  Coins,
  Database,
  DollarSign,
  FileText,
  Image,
  Instagram,
  LayoutDashboard,
  LayoutGrid,
  Mic,
  PartyPopper,
  Presentation,
  ServerCog,
  ShieldCheck,
  TrendingUp,
  Volume2,
  Webhook,
  Zap,
  type LucideIcon,
} from 'lucide-react'

export const ICONS: Record<string, LucideIcon> = {
  Activity,
  Bot,
  CheckCircle2,
  Code2,
  Coins,
  Database,
  DollarSign,
  FileText,
  Image,
  Instagram,
  LayoutDashboard,
  LayoutGrid,
  Mic,
  PartyPopper,
  Presentation,
  ServerCog,
  ShieldCheck,
  TrendingUp,
  Volume2,
  Webhook,
  Zap,
}

/** Resolve an icon key to a Lucide component, falling back to a neutral glyph. */
export function resolveIcon(key: string): LucideIcon {
  return ICONS[key] ?? Circle
}
