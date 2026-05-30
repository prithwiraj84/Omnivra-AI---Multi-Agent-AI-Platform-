import type { Config } from 'tailwindcss'
import animate from 'tailwindcss-animate'

/**
 * Omnivra Tailwind theme.
 *
 * Two layers live here:
 *  1. shadcn/ui semantic tokens (`hsl(var(--token))`) — bridged to the slate base via CSS vars
 *     declared in `src/index.css`. These power shadcn primitives (Button, Dialog, …).
 *  2. The Omnivra brand layer under the `omnivra-*` color namespace plus neon glows, glass blur,
 *     and motion keyframes. This is the authoritative styling layer (see docs/DESIGN_SYSTEM.md).
 *
 * Dark-only theme: `<html class="dark">` is always present; `:root` already holds the dark values.
 */
const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: { '2xl': '1600px' },
    },
    extend: {
      colors: {
        // --- shadcn/ui semantic bridge (slate base) ---
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },

        // --- Omnivra brand layer (authoritative) ---
        omnivra: {
          bg: '#0a0a0f',
          'bg-root': '#070a0f',
          sidebar: '#0a0e16',
          topbar: '#080c14',
          surface: '#0c1018',
          'surface-2': '#11151f',
          'surface-3': '#161b27',
          cyan: '#22d3ee',
          'cyan-dim': '#0e7490',
          purple: '#a855f7',
          violet: '#8b5cf6',
          indigo: '#6366f1',
          blue: '#3b82f6',
          emerald: '#10b981',
          'emerald-bright': '#34d399',
          amber: '#f59e0b',
          red: '#ef4444',
          pink: '#ec4899',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        omnivra: '16px',
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      backdropBlur: { xs: '4px', sm: '8px', glass: '12px', lg: '20px' },
      boxShadow: {
        card: '0 4px 24px -4px rgba(0,0,0,0.55)',
        panel: '0 8px 40px -8px rgba(0,0,0,0.65)',
        popover: '0 16px 48px -12px rgba(0,0,0,0.75)',
        'neon-cyan': '0 0 0 1px rgba(34,211,238,0.30), 0 0 20px -2px rgba(34,211,238,0.45)',
        'neon-violet': '0 0 0 1px rgba(168,85,247,0.30), 0 0 20px -2px rgba(168,85,247,0.45)',
        'neon-blue': '0 0 0 1px rgba(59,130,246,0.30), 0 0 20px -2px rgba(59,130,246,0.45)',
        'neon-emerald': '0 0 0 1px rgba(16,185,129,0.30), 0 0 20px -2px rgba(16,185,129,0.45)',
        // aliases matching docs/DESIGN_SYSTEM.md naming
        'glow-cyan': '0 0 0 1px rgba(34,211,238,0.30), 0 0 20px -2px rgba(34,211,238,0.45)',
        'glow-violet': '0 0 0 1px rgba(168,85,247,0.30), 0 0 20px -2px rgba(168,85,247,0.45)',
        'glow-blue': '0 0 0 1px rgba(59,130,246,0.30), 0 0 20px -2px rgba(59,130,246,0.45)',
        'glow-emerald': '0 0 0 1px rgba(16,185,129,0.30), 0 0 20px -2px rgba(16,185,129,0.45)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
        'glow-violet':
          'radial-gradient(60% 120% at 50% 0%, rgba(139,92,246,0.18), rgba(139,92,246,0.04) 45%, transparent 70%)',
        'glow-cyan':
          'radial-gradient(60% 120% at 50% 0%, rgba(34,211,238,0.16), rgba(34,211,238,0.03) 45%, transparent 70%)',
        'ambient':
          'radial-gradient(60% 120% at 20% 0%, rgba(139,92,246,0.10), transparent 60%), radial-gradient(50% 120% at 90% 10%, rgba(34,211,238,0.08), transparent 55%)',
      },
      transitionTimingFunction: {
        'out-quint': 'cubic-bezier(0.22,1,0.36,1)',
        'in-out-omni': 'cubic-bezier(0.4,0,0.2,1)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-dot': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.15)', opacity: '0.7' },
        },
        'pulse-slow': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.45', transform: 'scale(0.92)' },
        },
        glow: {
          '0%, 100%': { opacity: '1', filter: 'drop-shadow(0 0 6px rgba(34,211,238,0.55))' },
          '50%': { opacity: '0.82', filter: 'drop-shadow(0 0 14px rgba(34,211,238,0.95))' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.35s cubic-bezier(0.22,1,0.36,1)',
        'pulse-dot': 'pulse-dot 2s ease-in-out infinite',
        'pulse-slow': 'pulse-slow 2.6s ease-in-out infinite',
        glow: 'glow 2.4s ease-in-out infinite',
        shimmer: 'shimmer 2.5s linear infinite',
        float: 'float 4s ease-in-out infinite',
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
    },
  },
  plugins: [animate],
}

export default config
