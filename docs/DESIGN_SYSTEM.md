# Omnivra AI Company OS — Design System

> Single source of truth for the Omnivra UI. The goal is **same-to-same** parity with the
> reference dashboard (`Referance_Dashboard.png`): a dark, glassmorphic, neon-accented
> "AI company command center" (Claude Code × Devin × Linear × Vercel × Palantir × JARVIS).
>
> **Scope:** This document defines design **tokens**, the **component inventory**, and the
> **Tailwind/CSS utilities**. All values are calibrated against pixels sampled from the
> reference image and normalized to vivid, accessible neon accents.
>
> **Stack:** Vite + React + TypeScript + TailwindCSS + shadcn/ui + Framer Motion +
> React Flow + Recharts + Lucide Icons.

---

## 1. Design Principles

1. **Deep-space dark base.** Everything floats on a near-black navy (`#0a0a0f` / zinc-950).
   No pure black, no pure white. Surfaces are barely-lighter navy panels.
2. **Glass over glow.** Cards are translucent glass (`backdrop-blur-md`, ~1px white/8% border,
   soft drop shadow). Neon is an *accent*, never a fill — used for icons, dots, bars, chart
   strokes, focus rings, and hover glows.
3. **Four neon accents, one per semantic family.** Cyan = primary/active, Violet = AI/executive,
   Blue = info/in-progress, Emerald = success/online. Amber + Red are reserved for warning/danger.
4. **Quiet typography.** Inter/Geist. Headings white→zinc-100, body zinc-400, labels uppercase
   zinc-500 with wide tracking. Numbers are tabular and bold.
5. **Calm motion.** Short (150–300ms) ease-out transitions; subtle hover lift + glow; spring
   only for entrance/layout. Respect `prefers-reduced-motion`.

---

## 2. Color Tokens

All tokens are exported as CSS custom properties (`--omni-*`) and mirrored into the Tailwind
theme (`theme.extend.colors`). Hex values are authoritative; rgb channel triplets are provided
where a token is consumed via `rgb(var(--x) / <alpha>)` for opacity control.

### 2.1 Background / Surface Layers

| Token | Hex | Channels | Role |
|---|---|---|---|
| `bg.root` | `#070a0f` | `7 10 15` | App body, outermost canvas (deepest). |
| `bg.base` | `#0a0a0f` | `10 10 15` | Primary background (`zinc-950`-ish navy-black). |
| `bg.sidebar` | `#0a0e16` | `10 14 22` | Left sidebar / structural chrome. |
| `bg.topbar` | `#080c14` | `8 12 20` | Top bar (slightly darker than base). |
| `surface.1` | `#0c1018` | `12 16 24` | Card / panel base (raised one step). |
| `surface.2` | `#11151f` | `17 21 31` | Nested surface (inner rows, table headers, chips). |
| `surface.3` | `#161b27` | `22 27 39` | Hover / active surface, input fields. |
| `glass.fill` | `rgba(255,255,255,0.04)` | — | Glass card tint (over surface). |
| `glass.fill.strong` | `rgba(255,255,255,0.06)` | — | Stronger glass (modals, popovers). |

### 2.2 Borders & Dividers

| Token | Value | Role |
|---|---|---|
| `border.subtle` | `rgba(255,255,255,0.06)` | Default hairline divider. |
| `border.default` | `rgba(255,255,255,0.08)` | Card / glass border (1px). |
| `border.strong` | `rgba(255,255,255,0.12)` | Hover / focused card border. |
| `border.neon` | `rgba(34,211,238,0.35)` | Active / selected (cyan-tinted). |
| `ring.focus` | `#22d3ee` | Keyboard focus ring (cyan, 2px + glow). |

### 2.3 Neon Accents (+ soft-glow variants)

The four signature accents. Each ships a **base**, a **soft** (low-alpha fill for chips/track
fills), and a **glow** (box-shadow color). Glow variants are alpha colors for `box-shadow`.

| Family | Token | Hex | Channels | Soft (fill) | Glow (shadow) |
|---|---|---|---|---|---|
| **Cyber Cyan** (primary/active) | `accent.cyan` | `#22d3ee` | `34 211 238` | `rgba(34,211,238,0.12)` | `rgba(34,211,238,0.45)` |
| | `accent.cyan.dim` | `#0e7490` | `14 116 144` | — | — |
| **Neon Violet** (AI/executive) | `accent.violet` | `#a855f7` | `168 85 247` | `rgba(168,85,247,0.12)` | `rgba(168,85,247,0.45)` |
| | `accent.violet.alt` | `#8b5cf6` | `139 92 246` | `rgba(139,92,246,0.12)` | `rgba(139,92,246,0.40)` |
| **Electric Blue** (info/in-progress) | `accent.blue` | `#3b82f6` | `59 130 246` | `rgba(59,130,246,0.12)` | `rgba(59,130,246,0.45)` |
| **Emerald** (success/online) | `accent.emerald` | `#10b981` | `16 185 129` | `rgba(16,185,129,0.12)` | `rgba(16,185,129,0.45)` |
| | `accent.emerald.bright` | `#34d399` | `52 211 153` | — | — |

> **Indigo note.** The active sidebar item in the reference is an indigo fill (sampled ~`#3b30ac`).
> We render it as a violet→indigo gradient (`accent.violet` → `#6366f1`) for the active nav pill,
> see §7 `.nav-active`.

### 2.4 Semantic Colors

| Token | Hex | Channels | Use |
|---|---|---|---|
| `success` | `#10b981` | `16 185 129` | Online, Completed, positive deltas, "Excellent". |
| `success.soft` | `rgba(16,185,129,0.12)` | — | Success badge bg. |
| `warning` | `#f59e0b` | `245 158 11` | Medium priority, quotas nearing limit. |
| `warning.soft` | `rgba(245,158,11,0.12)` | — | Warning badge bg. |
| `danger` | `#ef4444` | `239 68 68` | High priority, Failed, errors. |
| `danger.soft` | `rgba(239,68,68,0.12)` | — | Danger badge bg. |
| `info` | `#3b82f6` | `59 130 246` | Running, In Progress, informational. |
| `info.soft` | `rgba(59,130,246,0.12)` | — | Info badge bg. |

### 2.5 Text Colors

| Token | Hex | Use |
|---|---|---|
| `text.primary` | `#fafafa` | Headings, stat values, primary content (zinc-50). |
| `text.secondary` | `#e4e4e7` | Strong body, agent names (zinc-200). |
| `text.muted` | `#a1a1aa` | Body, descriptions (zinc-400). |
| `text.faint` | `#71717a` | Captions, model names, timestamps (zinc-500). |
| `text.label` | `#52525b` | Uppercase section labels (zinc-600, tracked). |
| `text.on-accent` | `#06060a` | Text on filled accent (dark). |

### 2.6 Chart Palette

Used by Recharts (area + donut) and progress bars. Calibrated to the reference chart strokes.

**Area chart (Task Execution Overview)** — stroke + gradient fill (top alpha → 0):

| Series | Stroke | Gradient top | Gradient bottom |
|---|---|---|---|
| Completed | `#10b981` | `rgba(16,185,129,0.35)` | `rgba(16,185,129,0)` |
| In Progress | `#3b82f6` | `rgba(59,130,246,0.30)` | `rgba(59,130,246,0)` |
| Failed | `#ef4444` | `rgba(239,68,68,0.25)` | `rgba(239,68,68,0)` |

**Donut chart (Task Distribution)** — categorical, ordered:

| Index | Category (example) | Hex |
|---|---|---|
| 0 | Development | `#22d3ee` (cyan) |
| 1 | Marketing | `#a855f7` (violet) |
| 2 | Documentation | `#3b82f6` (blue) |
| 3 | Quality & Security | `#f59e0b` (amber) |
| 4 | System Ops | `#10b981` (emerald) |
| 5 | (overflow) | `#ec4899` (pink) |
| 6 | (overflow) | `#8b5cf6` (violet-alt) |

Donut track (unfilled / gap): `rgba(255,255,255,0.04)`. Center label: `text.primary`.

**Progress / usage bars** — bar track `rgba(255,255,255,0.06)`; fills cycle the categorical
palette above (cyan → violet → blue → amber → emerald → pink).

---

## 3. Typography

### 3.1 Font Stack

```
--font-sans: "Inter", "Geist", ui-sans-serif, system-ui, -apple-system,
             "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
--font-mono: "Geist Mono", "JetBrains Mono", ui-monospace,
             SFMono-Regular, Menlo, Consolas, monospace;
```

- **Inter** (or **Geist**) is the primary UI face. Load `400 / 500 / 600 / 700`.
- **Geist Mono / JetBrains Mono** for the ⌘K hint, code, model IDs, log lines, and the
  clock readout in the right rail.
- Enable `font-feature-settings: "cv11", "ss01"; font-variant-numeric: tabular-nums;`
  on numeric stat values for aligned digits.

### 3.2 Type Scale

| Token | Size / Line | Weight | Tracking | Usage |
|---|---|---|---|---|
| `display` | 30px / 36px | 700 | -0.02em | "Good morning, Omnivra!" greeting. |
| `h1` | 24px / 32px | 700 | -0.01em | Page titles. |
| `h2` | 18px / 26px | 600 | -0.01em | Section / card titles. |
| `h3` | 15px / 22px | 600 | 0 | Subsection, agent card name. |
| `stat` | 26px / 30px | 700 | -0.01em | Stat card values (tabular-nums). |
| `body` | 14px / 21px | 400 | 0 | Default body text. |
| `body-sm` | 13px / 19px | 400 | 0 | Dense rows, descriptions. |
| `label` | 11px / 14px | 600 | 0.08em | UPPERCASE section labels (zinc-500/600). |
| `caption` | 12px / 16px | 400 | 0 | Timestamps, model names, hints. |
| `badge` | 11px / 14px | 600 | 0.02em | Pills / status badges. |
| `mono-sm` | 12px / 16px | 500 | 0 | ⌘K hint, log lines, IDs. |

---

## 4. Spacing, Sizing & Layout

### 4.1 Spacing scale (4px base)

`0, 1=4, 2=8, 3=12, 4=16, 5=20, 6=24, 8=32, 10=40, 12=48, 16=64`.
Default card padding `p-5` (20px); compact rows `p-3`/`p-4`; section gap `gap-5`/`gap-6`.

### 4.2 Layout grid

| Token | Value | Role |
|---|---|---|
| `layout.sidebar.w` | `248px` | Fixed left sidebar width. |
| `layout.topbar.h` | `60px` | Fixed top bar height. |
| `layout.rightrail.w` | `320px` | Right rail width (clock, approvals, health). |
| `layout.content.max` | `1600px` | Max content width before centering. |
| `layout.gutter` | `24px` | Outer page padding. |
| `grid.stats` | 5 cols | Executive Overview stat cards (responsive → 2 → 1). |
| `grid.agents` | 5 cols | AI Agents Status grid (responsive → 3 → 2 → 1). |
| `grid.charts` | `1.4fr 1.4fr 1fr` | Workflows · Area chart · Donut (responsive stack). |
| `grid.bottom` | `1fr 1fr 1fr` | Model Usage · Top Models · Media Services. |

### 4.3 Border Radius

| Token | px | Use |
|---|---|---|
| `radius.sm` | 8 | Badges, chips, small buttons. |
| `radius.md` | 12 | Inputs, icon tiles, nav items. |
| `radius.lg` | 16 | Cards / panels (default). |
| `radius.xl` | 20 | Large hero / brand cards. |
| `radius.full` | 9999 | Status dots, pills, avatars. |

### 4.4 Icon tiles & dots

| Token | Value | Use |
|---|---|---|
| `tile.agent` | `40px`, `radius.md` | Agent card icon container (tinted accent bg). |
| `tile.stat` | `36px`, `radius.md` | Stat / activity icon container. |
| `dot.status` | `8px`, `radius.full` | Online/offline status dot (+ glow). |
| `dot.legend` | `8px`, `radius.full` | Chart legend dot. |

---

## 5. Elevation: Shadows & Glows

Shadows are soft and low-contrast (dark UI). Glows are colored, used on hover / active / focus.

| Token | Value |
|---|---|
| `shadow.sm` | `0 1px 2px rgba(0,0,0,0.40)` |
| `shadow.card` | `0 4px 24px -4px rgba(0,0,0,0.55)` |
| `shadow.panel` | `0 8px 40px -8px rgba(0,0,0,0.65)` |
| `shadow.popover` | `0 16px 48px -12px rgba(0,0,0,0.75)` |
| `glow.cyan` | `0 0 0 1px rgba(34,211,238,0.30), 0 0 20px -2px rgba(34,211,238,0.45)` |
| `glow.violet` | `0 0 0 1px rgba(168,85,247,0.30), 0 0 20px -2px rgba(168,85,247,0.45)` |
| `glow.blue` | `0 0 0 1px rgba(59,130,246,0.30), 0 0 20px -2px rgba(59,130,246,0.45)` |
| `glow.emerald` | `0 0 0 1px rgba(16,185,129,0.30), 0 0 20px -2px rgba(16,185,129,0.45)` |
| `glow.dot` | `0 0 8px 0 currentColor` (apply on status dot via accent text color) |
| `inset.top` | `inset 0 1px 0 0 rgba(255,255,255,0.05)` (glass top highlight) |

### Blur levels (backdrop)

| Token | px |
|---|---|
| `blur.sm` | 8 |
| `blur.md` | 12 (default glass) |
| `blur.lg` | 20 (modals/popovers) |

---

## 6. Motion Tokens (Framer Motion)

| Token | Value | Use |
|---|---|---|
| `dur.fast` | `0.15s` | Hover color/opacity, badge, dot pulse step. |
| `dur.base` | `0.22s` | Default transitions (card hover lift, nav). |
| `dur.slow` | `0.35s` | Panel entrance, chart reveal. |
| `dur.xslow` | `0.6s` | Hero/greeting, staged dashboard mount. |
| `ease.out` | `[0.22, 1, 0.36, 1]` | Standard ease-out (entrances). |
| `ease.inout` | `[0.4, 0, 0.2, 1]` | Symmetric transitions. |
| `ease.spring` | `{ type: "spring", stiffness: 320, damping: 30 }` | Layout / list reorder. |
| `stagger.children` | `0.05s` | Stat cards / agent grid stagger. |
| `motion.cardHover` | `y: -2, boxShadow: glow.cyan` | Interactive card hover. |
| `motion.fadeUp` | `from {opacity:0, y:8}` → `{opacity:1, y:0}` | Default item entrance. |
| `motion.pulse` | scale `1 → 1.15 → 1`, `dur.slow`, `repeat: Infinity` | Online dot pulse, live feed badge. |

> **Accessibility:** wrap entrance/looping animations in a `useReducedMotion()` guard; when
> reduced, drop transforms and infinite loops, keep opacity-only fades ≤ `dur.fast`.

---

## 7. Tailwind / CSS Utilities (glass + neon)

These classes belong in `src/index.css` (`@layer components` / `@layer utilities`). They depend
on the CSS variables defined in §2 (emit them under `:root`). Drop-in for the frontend architect.

### 7.1 CSS variables (`:root`)

```css
:root {
  /* backgrounds */
  --omni-bg-root: #070a0f;
  --omni-bg-base: #0a0a0f;
  --omni-bg-sidebar: #0a0e16;
  --omni-bg-topbar: #080c14;
  --omni-surface-1: #0c1018;
  --omni-surface-2: #11151f;
  --omni-surface-3: #161b27;

  /* borders */
  --omni-border-subtle: 255 255 255;   /* use with / <alpha> */
  --omni-border: rgba(255,255,255,0.08);
  --omni-border-strong: rgba(255,255,255,0.12);

  /* accents (channel triplets for rgb(var(--x) / a)) */
  --omni-cyan: 34 211 238;
  --omni-violet: 168 85 247;
  --omni-violet-alt: 139 92 246;
  --omni-blue: 59 130 246;
  --omni-emerald: 16 185 129;
  --omni-amber: 245 158 11;
  --omni-red: 239 68 68;
  --omni-pink: 236 72 153;

  /* text */
  --omni-text: #fafafa;
  --omni-text-muted: #a1a1aa;
  --omni-text-faint: #71717a;

  /* radii */
  --omni-radius: 16px;

  /* fonts */
  --font-sans: "Inter","Geist",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --font-mono: "Geist Mono","JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}

html, body, #root { background: var(--omni-bg-base); color: var(--omni-text); font-family: var(--font-sans); }
```

### 7.2 Component / utility classes

```css
@layer components {
  /* --- Glass primitive --- */
  .glass {
    background-color: rgba(255,255,255,0.04);
    border: 1px solid var(--omni-border);
    border-radius: var(--omni-radius);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 4px 24px -4px rgba(0,0,0,0.55), inset 0 1px 0 0 rgba(255,255,255,0.05);
  }
  .glass-strong {
    background-color: rgba(255,255,255,0.06);
    border: 1px solid var(--omni-border-strong);
    border-radius: var(--omni-radius);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 16px 48px -12px rgba(0,0,0,0.75), inset 0 1px 0 0 rgba(255,255,255,0.06);
  }
  /* Solid panel (no transparency) — for charts where blur over content is undesirable */
  .panel {
    background-color: var(--omni-surface-1);
    border: 1px solid var(--omni-border);
    border-radius: var(--omni-radius);
    box-shadow: 0 4px 24px -4px rgba(0,0,0,0.55);
  }
  .panel-inset { background-color: var(--omni-surface-2); border-radius: 12px; }

  /* --- Section label --- */
  .section-label {
    font-size: 11px; line-height: 14px; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; color: var(--omni-text-faint);
  }

  /* --- Active nav pill (violet→indigo, matches reference) --- */
  .nav-item { border-radius: 12px; color: var(--omni-text-muted); transition: all .22s; }
  .nav-item:hover { background: var(--omni-surface-2); color: var(--omni-text); }
  .nav-active {
    color: #fff;
    background: linear-gradient(90deg, rgba(139,92,246,0.95), rgba(99,102,241,0.95));
    box-shadow: 0 0 0 1px rgba(168,85,247,0.40), 0 4px 18px -4px rgba(139,92,246,0.55);
  }

  /* --- Status dot with glow --- */
  .status-dot {
    width: 8px; height: 8px; border-radius: 9999px;
    background: currentColor; box-shadow: 0 0 8px 0 currentColor;
  }

  /* --- Badges --- */
  .badge { display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:8px;
           font-size:11px; font-weight:600; line-height:14px; border:1px solid transparent; }
  .badge-success { color:#34d399; background:rgba(16,185,129,0.12); border-color:rgba(16,185,129,0.25); }
  .badge-info    { color:#60a5fa; background:rgba(59,130,246,0.12); border-color:rgba(59,130,246,0.25); }
  .badge-warning { color:#fbbf24; background:rgba(245,158,11,0.12); border-color:rgba(245,158,11,0.25); }
  .badge-danger  { color:#f87171; background:rgba(239,68,68,0.12);  border-color:rgba(239,68,68,0.25); }
  .badge-cyan    { color:#22d3ee; background:rgba(34,211,238,0.12); border-color:rgba(34,211,238,0.25); }
  .badge-violet  { color:#c084fc; background:rgba(168,85,247,0.12); border-color:rgba(168,85,247,0.25); }
}

@layer utilities {
  /* --- Neon glows (hover/active/focus) --- */
  .glow-cyan    { box-shadow: 0 0 0 1px rgba(34,211,238,0.30), 0 0 20px -2px rgba(34,211,238,0.45); }
  .glow-violet  { box-shadow: 0 0 0 1px rgba(168,85,247,0.30), 0 0 20px -2px rgba(168,85,247,0.45); }
  .glow-blue    { box-shadow: 0 0 0 1px rgba(59,130,246,0.30), 0 0 20px -2px rgba(59,130,246,0.45); }
  .glow-emerald { box-shadow: 0 0 0 1px rgba(16,185,129,0.30), 0 0 20px -2px rgba(16,185,129,0.45); }

  /* --- Accent icon tiles (tinted bg + colored icon) --- */
  .tile-cyan    { background:rgba(34,211,238,0.12);  color:#22d3ee; }
  .tile-violet  { background:rgba(168,85,247,0.12);  color:#c084fc; }
  .tile-blue    { background:rgba(59,130,246,0.12);  color:#60a5fa; }
  .tile-emerald { background:rgba(16,185,129,0.12);  color:#34d399; }
  .tile-amber   { background:rgba(245,158,11,0.12);  color:#fbbf24; }
  .tile-pink    { background:rgba(236,72,153,0.12);  color:#f472b6; }

  /* --- Focus ring --- */
  .focus-ring:focus-visible { outline:none; box-shadow:0 0 0 2px var(--omni-bg-base),
                              0 0 0 4px rgba(34,211,238,0.70), 0 0 16px -2px rgba(34,211,238,0.6); }

  /* --- Hairline gradient divider --- */
  .divider-x { height:1px; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.10),transparent); }

  /* --- Subtle ambient radial glow behind hero / brand card --- */
  .ambient-glow { background:
    radial-gradient(60% 120% at 20% 0%, rgba(139,92,246,0.10), transparent 60%),
    radial-gradient(50% 120% at 90% 10%, rgba(34,211,238,0.08), transparent 55%); }

  /* --- Animated progress bar fill (use accent color via --bar) --- */
  .progress-track { background:rgba(255,255,255,0.06); border-radius:9999px; height:6px; overflow:hidden; }
  .progress-fill  { height:100%; border-radius:9999px; background:var(--bar,#22d3ee);
                    box-shadow:0 0 8px -1px var(--bar,#22d3ee); transition:width .6s cubic-bezier(.22,1,.36,1); }

  /* scrollbars */
  .scroll-thin::-webkit-scrollbar { width:8px; height:8px; }
  .scroll-thin::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.10); border-radius:9999px; }
  .scroll-thin::-webkit-scrollbar-track { background:transparent; }
}
```

### 7.3 `tailwind.config.ts` theme.extend snippet

```ts
extend: {
  colors: {
    bg: { root:'#070a0f', base:'#0a0a0f', sidebar:'#0a0e16', topbar:'#080c14' },
    surface: { 1:'#0c1018', 2:'#11151f', 3:'#161b27' },
    cyan:    { DEFAULT:'#22d3ee', dim:'#0e7490' },
    violet:  { DEFAULT:'#a855f7', alt:'#8b5cf6' },
    electric:{ DEFAULT:'#3b82f6' },
    emerald: { DEFAULT:'#10b981', bright:'#34d399' },
    success:'#10b981', warning:'#f59e0b', danger:'#ef4444', info:'#3b82f6',
    'text-muted':'#a1a1aa', 'text-faint':'#71717a',
  },
  borderRadius: { sm:'8px', md:'12px', lg:'16px', xl:'20px' },
  fontFamily: { sans:['Inter','Geist','ui-sans-serif','system-ui'], mono:['Geist Mono','JetBrains Mono','ui-monospace'] },
  backdropBlur: { sm:'8px', md:'12px', lg:'20px' },
  boxShadow: {
    card:'0 4px 24px -4px rgba(0,0,0,0.55)',
    panel:'0 8px 40px -8px rgba(0,0,0,0.65)',
    popover:'0 16px 48px -12px rgba(0,0,0,0.75)',
    'glow-cyan':'0 0 0 1px rgba(34,211,238,0.30), 0 0 20px -2px rgba(34,211,238,0.45)',
    'glow-violet':'0 0 0 1px rgba(168,85,247,0.30), 0 0 20px -2px rgba(168,85,247,0.45)',
    'glow-blue':'0 0 0 1px rgba(59,130,246,0.30), 0 0 20px -2px rgba(59,130,246,0.45)',
    'glow-emerald':'0 0 0 1px rgba(16,185,129,0.30), 0 0 20px -2px rgba(16,185,129,0.45)',
  },
  transitionTimingFunction: { 'out-quint':'cubic-bezier(0.22,1,0.36,1)' },
  keyframes: {
    'fade-up': { '0%':{opacity:'0',transform:'translateY(8px)'},'100%':{opacity:'1',transform:'translateY(0)'} },
    'pulse-dot': { '0%,100%':{transform:'scale(1)',opacity:'1'},'50%':{transform:'scale(1.15)',opacity:'0.7'} },
  },
  animation: { 'fade-up':'fade-up .35s cubic-bezier(0.22,1,0.36,1)', 'pulse-dot':'pulse-dot 2s ease-in-out infinite' },
}
```

---

## 8. Component Inventory

Maps **every reference-dashboard region** to a concrete component. Two layers:
**UI primitives** (`src/components/ui/`, built once, reused everywhere — **Phase 2**) and
**dashboard sections** (`src/components/dashboard/`, compose primitives — **Phase 3**).

### 8.1 UI Primitives — Phase 2 (`src/components/ui/`)

| Component | File | Renders / Region | Key Props | Accents |
|---|---|---|---|---|
| `GlassCard` | `glass-card.tsx` | Base surface for all cards/panels | `variant?: 'glass'\|'glass-strong'\|'panel'`, `glow?: Accent`, `interactive?`, `padding?`, `as?` | any (via `glow`) |
| `NeonBadge` | `neon-badge.tsx` | Status/priority pills everywhere | `tone: 'success'\|'info'\|'warning'\|'danger'\|'cyan'\|'violet'`, `dot?`, `children` | semantic |
| `StatusDot` | `status-dot.tsx` | "Online"/"Offline" indicators | `status: 'online'\|'offline'\|'busy'\|'idle'`, `pulse?`, `label?` | emerald / amber / red |
| `IconTile` | `icon-tile.tsx` | Tinted square behind agent/stat/activity icons | `accent: Accent`, `size?: 'sm'\|'md'`, `icon: LucideIcon` | all 6 tiles |
| `ProgressBar` | `progress-bar.tsx` | Workflow + system-health + usage bars | `value:number`, `accent?: Accent`, `showLabel?`, `track?` | cyan/violet/blue/amber/emerald |
| `SectionHeader` | `section-header.tsx` | "AI AGENTS STATUS", "ACTIVE WORKFLOWS" labels + action | `label`, `action?: ReactNode`, `count?` | cyan (action link) |
| `Sparkline` | `sparkline.tsx` | Mini line in brand footer / inline trends | `data:number[]`, `accent?` | violet |
| `Pill` / `Chip` | `chip.tsx` | System-ops mini agent chips, filters | `label`, `icon?`, `accent?`, `active?` | cyan/emerald |
| `KbdHint` | `kbd-hint.tsx` | ⌘K hint in search | `keys:string[]` | — (mono) |
| `Avatar` | `avatar.tsx` | User avatar (topbar, footer card) | `src?`, `fallback`, `online?` | emerald dot |
| `IconButton` | `icon-button.tsx` | Bell / settings / menu in topbar | `icon`, `badge?:number`, `aria-label` | red badge |
| `TimeframeSelect` | `timeframe-select.tsx` | "Daily" dropdown on charts | `value`, `options`, `onChange` | cyan focus |
| `Tooltip` | `tooltip.tsx` | Chart/agent hover tooltips (shadcn wrap) | standard | — |
| `EmptyState` | `empty-state.tsx` | Empty feeds/lists | `icon`, `title`, `hint?` | violet |
| `ScrollArea` | `scroll-area.tsx` | Thin-scroll wrapper for feeds/lists | `maxHeight` | — |

> **Charts (primitives, Phase 2)** — thin Recharts wrappers that consume the chart palette:
> | `AreaChart` | `charts/area-chart.tsx` | Task Execution Overview | `series:{key,color,label}[]`, `data`, `xKey` | emerald/blue/red |
> | `DonutChart` | `charts/donut-chart.tsx` | Task Distribution | `data:{name,value,color}[]`, `centerValue`, `centerLabel` | categorical |
> | `BarMeter` | `charts/bar-meter.tsx` | Model/provider usage horizontal bars | `rows:{label,value,pct,color}[]` | categorical |

### 8.2 Dashboard Sections — Phase 3 (`src/components/dashboard/`)

| Component | File | Reference Region | Key Props | Composes | Accents |
|---|---|---|---|---|---|
| `Sidebar` | `sidebar.tsx` | Fixed left nav (logo, nav, DEPARTMENTS, SYSTEM, user card + storage) | `nav`, `departments`, `system`, `user`, `storagePct` | `nav-item`/`nav-active`, `StatusDot`, `ProgressBar` | violet (active), emerald |
| `BrandLogo` | `brand-logo.tsx` | "OMNIVRA / AI Company OS V2.0" mark | `version?` | — | violet gradient |
| `Topbar` | `topbar.tsx` | Global search ⌘K, bell[badge], settings, avatar | `notifications:number`, `onSearch` | `IconButton`,`KbdHint`,`Avatar` | red badge, cyan focus |
| `RightRail` | `right-rail.tsx` | Clock/date, "All Systems Operational", Pending Approvals, System Health | `time`,`systemStatus`,`approvals`,`health` | `PendingApprovals`,`SystemHealth`,`NeonBadge` | emerald, mono clock |
| `GreetingHero` | `greeting-hero.tsx` | "Good morning, Omnivra! 👋 …full capacity." | `name`,`subtitle` | `ambient-glow` | violet/cyan ambient |
| `StatCard` | `stat-card.tsx` | Executive Overview cards (Total Agents/Active Tasks/Completed/Success Rate/Total Cost) | `label`,`value`,`delta?`,`deltaTone?`,`hint?`,`icon`,`accent` | `GlassCard`,`IconTile`,`NeonBadge` | emerald/blue/violet |
| `ExecutiveOverview` | `executive-overview.tsx` | The 5-card stat row container | `stats: StatCardProps[]` | `StatCard` ×5 | mixed |
| `AgentCard` | `agent-card.tsx` | One agent tile (icon, name, dept, model, online dot) | `name`,`department`,`model`,`provider`,`accent`,`status` | `GlassCard`,`IconTile`,`StatusDot` | per-dept accent |
| `AgentStatusGrid` | `agent-status-grid.tsx` | "AI AGENTS STATUS" grid + "View All Agents" | `agents: AgentCardProps[]`, `onViewAll` | `SectionHeader`,`AgentCard`,`SystemOpsRow` | mixed |
| `SystemOpsRow` | `system-ops-row.tsx` | "SYSTEM OPERATIONS" chip sub-row (Task Classifier…Log Analyzer) | `ops:{name,icon,status}[]` | `Chip`,`StatusDot` | cyan/emerald |
| `WorkflowList` | `workflow-list.tsx` | "ACTIVE WORKFLOWS" container + "View All" | `workflows: WorkflowRowProps[]` | `SectionHeader`,`WorkflowRow` | mixed |
| `WorkflowRow` | `workflow-row.tsx` | One workflow (icon, name, dept, status pill, progress %) | `name`,`department`,`status`,`progress`,`accent` | `IconTile`,`NeonBadge`,`ProgressBar` | cyan/violet/blue/amber/emerald |
| `TaskExecutionChart` | `task-execution-chart.tsx` | "TASK EXECUTION OVERVIEW" area chart + timeframe | `data`,`timeframe`,`onTimeframeChange` | `GlassCard`,`AreaChart`,`TimeframeSelect` | emerald/blue/red |
| `TaskDistribution` | `task-distribution.tsx` | "TASK DISTRIBUTION" donut + legend (124 Total Tasks) | `segments`,`total` | `GlassCard`,`DonutChart`,legend dots | categorical |
| `ActivityFeed` | `activity-feed.tsx` | "LIVE ACTIVITY FEED" (icon, agent, action, timestamp) | `items: ActivityItem[]`, `live?` | `IconTile`,`ScrollArea`,`pulse-dot` | per-agent accent |
| `PendingApprovals` | `pending-approvals.tsx` | "PENDING APPROVALS" (priority badge + Review) — also right rail | `items: ApprovalItem[]`, `onReview` | `ApprovalCard` | red/amber priority, cyan btn |
| `ApprovalCard` | `approval-card.tsx` | One approval row (title, source, priority, Review/Approve/Reject/Retry/Rollback) | `title`,`source`,`priority`,`actions`,`onAction` | `NeonBadge`,`IconButton` | danger/warning, cyan |
| `SystemHealth` | `system-health.tsx` | "SYSTEM HEALTH" (CPU/Memory/Storage/Network/API quotas) | `metrics:{label,pct,tone}[]` | `ProgressBar`,`NeonBadge` | emerald→amber→red by load |
| `ProviderUsageBar` | `provider-usage.tsx` | "MODEL USAGE BY PROVIDER" (Google/OpenRouter/Groq/HF bars) | `providers:{name,pct,calls,color}[]` | `BarMeter` | categorical |
| `ModelUsageRow` | `model-usage.tsx` | "TOP MODELS BY USAGE" rows (model id + calls + bar) | `models:{id,calls,pct,color}[]`, `onViewAll` | `BarMeter`,`SectionHeader` | categorical |
| `MediaServiceCard` | `media-service-card.tsx` | "MEDIA SERVICES" (STT/TTS/Image Gen, status, calls) | `name`,`provider`,`status`,`calls`,`accent`,`icon` | `GlassCard`,`IconTile`,`NeonBadge` | cyan/violet/emerald |
| `AchievementCard` | `achievement-card.tsx` | "RECENT ACHIEVEMENTS" row (100+ Tasks, 98.6% Success…) | `icon`,`title`,`subtitle`,`accent` | `GlassCard`,`IconTile` | mixed |
| `BrandFooterCard` | `brand-footer-card.tsx` | "Omnivra AI Company OS — The World's First AI Native Company OS" + sparkline | `tagline`,`trend` | `GlassCard`(xl),`Sparkline`,`ambient-glow` | violet→indigo gradient |
| `DashboardGrid` | `dashboard-grid.tsx` | Page-level layout assembling all sections | — | all of the above | — |

### 8.3 Future-Phase Sections (manifest only — built later)

| Component | File | Region | Phase |
|---|---|---|---|
| `AgentHierarchyTree` | `dashboard/agent-hierarchy-tree.tsx` | CEO → departments → agents (React Flow) | Phase 4 |
| `MemoryUsagePanel` | `dashboard/memory-usage.tsx` | Memory Usage view | Phase 4 |
| `SecurityCenter` | `dashboard/security-center.tsx` | Security Center view | Phase 5 |
| `DocumentationCenter` | `dashboard/documentation-center.tsx` | Documentation Center | Phase 5 |
| `MarketingCenter` | `dashboard/marketing-center.tsx` | Marketing Center | Phase 5 |
| `RecoveryStatus` | `dashboard/recovery-status.tsx` | Recovery / checkpoint status | Phase 5 |

---

## 9. Accent → Department Mapping

Keeps agent icons / cards color-coded consistently across the dashboard.

| Department | Accent | Tile class |
|---|---|---|
| Executive (CEO) | Cyan `#22d3ee` | `.tile-cyan` |
| Architecture | Violet `#a855f7` | `.tile-violet` |
| Design | Pink `#ec4899` | `.tile-pink` |
| Engineering | Blue `#3b82f6` | `.tile-blue` |
| Quality & Security | Emerald `#10b981` | `.tile-emerald` |
| Marketing | Amber `#f59e0b` | `.tile-amber` |
| Documentation | Violet-alt `#8b5cf6` | `.tile-violet` |
| System Ops | Cyan `#22d3ee` | `.tile-cyan` |
| Media | Emerald / Cyan | `.tile-emerald` |

---

## 10. Implementation Notes

- **Token source of truth:** generate `src/styles/tokens.ts` from §2–§6 and re-use in Recharts
  (which needs JS, not CSS vars) so charts and CSS never drift.
- **shadcn/ui:** install with the **slate/zinc** base, then override CSS variables to the Omnivra
  palette in §7.1. Keep shadcn component anatomy; only restyle via these tokens/classes.
- **Glass vs panel:** use `.glass` for stat/agent/approval/media/achievement cards (translucent
  over the ambient background). Use `.panel` (opaque) for the **chart** containers so Recharts
  gradients render on a stable backdrop.
- **Contrast:** body text uses `text.muted` (#a1a1aa) on `surface.1` → ratio ≈ 6.3:1 (AA).
  Never place neon accent text smaller than 13px on glass without bumping to the `.bright` variant.
- **Reduced motion:** all §6 looping/spring animations must be gated by `useReducedMotion()`.
