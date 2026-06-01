import { useMemo, useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Code2,
  FileCode,
  FileText,
  Folder,
  FolderOpen,
  Loader2,
  Play,
  Presentation,
  ScrollText,
  Terminal,
  type LucideIcon,
} from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ScrollArea } from '@/components/ui/scroll-area'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { EmptyState } from '@/components/ui/empty-state'
import { Button } from '@/components/ui/button'
import { useArtifacts, useArtifact, useRunProgram } from '@/hooks/useArtifacts'
import { isRunnable } from '@/lib/api/artifacts'
import { cn } from '@/lib/utils'
import type { Accent } from '@/types'
import type { Artifact } from '@/lib/api/types'

export interface ArtifactExplorerProps {
  /** Restrict the list to one workspace category (e.g. "docs"). Omit for all. */
  category?: string
  /** SectionHeader title (e.g. "Workspace Artifacts"). */
  title: string
}

interface CategoryStyle {
  icon: LucideIcon
  accent: Accent
  tone: BadgeTone
}

const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  frontend: { icon: Code2, accent: 'blue', tone: 'info' },
  backend: { icon: FileCode, accent: 'violet', tone: 'violet' },
  docs: { icon: FileText, accent: 'cyan', tone: 'cyan' },
  presentations: { icon: Presentation, accent: 'pink', tone: 'warning' },
  reports: { icon: ScrollText, accent: 'emerald', tone: 'success' },
}
const DEFAULT_STYLE: CategoryStyle = { icon: Folder, accent: 'cyan', tone: 'info' }
const styleFor = (category: string): CategoryStyle => CATEGORY_STYLES[category] ?? DEFAULT_STYLE

// --- file tree ----------------------------------------------------------------
interface TreeNode {
  name: string
  path: string // full workspace-relative path (files) or folder prefix
  isFile: boolean
  artifact?: Artifact
  children: Map<string, TreeNode>
}

/** Build a nested folder tree from the flat artifact list (so generated code reads as a codebase). */
function buildTree(artifacts: Artifact[]): TreeNode {
  const root: TreeNode = { name: '', path: '', isFile: false, children: new Map() }
  for (const art of artifacts) {
    const parts = art.path.split('/').filter(Boolean)
    let node = root
    parts.forEach((part, i) => {
      const isFile = i === parts.length - 1
      const path = parts.slice(0, i + 1).join('/')
      let child = node.children.get(part)
      if (!child) {
        child = { name: part, path, isFile, children: new Map() }
        node.children.set(part, child)
      }
      if (isFile) child.artifact = art
      node = child
    })
  }
  return root
}

/** Folders first, then files; each alphabetical. */
function sortedChildren(node: TreeNode): TreeNode[] {
  return [...node.children.values()].sort((a, b) => {
    if (a.isFile !== b.isFile) return a.isFile ? 1 : -1
    return a.name.localeCompare(b.name)
  })
}

/** All folder paths (so the tree starts fully expanded). */
function allFolderPaths(node: TreeNode, acc: Set<string> = new Set()): Set<string> {
  for (const child of node.children.values()) {
    if (!child.isFile) {
      acc.add(child.path)
      allFolderPaths(child, acc)
    }
  }
  return acc
}

function formatModified(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function TreeRows({
  node,
  depth,
  expanded,
  toggle,
  selectedPath,
  onSelect,
}: {
  node: TreeNode
  depth: number
  expanded: Set<string>
  toggle: (path: string) => void
  selectedPath: string | null
  onSelect: (path: string) => void
}) {
  return (
    <>
      {sortedChildren(node).map((child) => {
        const pad = { paddingLeft: `${depth * 14 + 8}px` }
        if (child.isFile) {
          const style = styleFor(child.artifact?.category ?? '')
          const selected = child.path === selectedPath
          return (
            <button
              key={child.path}
              type="button"
              onClick={() => onSelect(child.path)}
              aria-current={selected}
              style={pad}
              className={cn(
                'flex w-full items-center gap-2 rounded-md py-1.5 pr-2 text-left text-sm transition-colors',
                'hover:bg-white/[0.04]',
                selected ? 'bg-white/[0.07] text-[#fafafa]' : 'text-[#d4d4d8]',
              )}
            >
              <style.icon className={cn('h-4 w-4 shrink-0', selected ? 'text-omnivra-cyan' : 'text-[#71717a]')} aria-hidden />
              <span className="min-w-0 flex-1 truncate">{child.name}</span>
              {isRunnable(child.path) && <Play className="h-3 w-3 shrink-0 text-omnivra-emerald/70" aria-hidden />}
            </button>
          )
        }
        const open = expanded.has(child.path)
        return (
          <div key={child.path}>
            <button
              type="button"
              onClick={() => toggle(child.path)}
              aria-expanded={open}
              style={pad}
              className="flex w-full items-center gap-1.5 rounded-md py-1.5 pr-2 text-left text-sm font-medium text-[#a1a1aa] transition-colors hover:bg-white/[0.03]"
            >
              {open ? <ChevronDown className="h-3.5 w-3.5 shrink-0" aria-hidden /> : <ChevronRight className="h-3.5 w-3.5 shrink-0" aria-hidden />}
              {open ? <FolderOpen className="h-4 w-4 shrink-0 text-omnivra-amber" aria-hidden /> : <Folder className="h-4 w-4 shrink-0 text-omnivra-amber" aria-hidden />}
              <span className="min-w-0 flex-1 truncate">{child.name}</span>
            </button>
            {open && (
              <TreeRows
                node={child}
                depth={depth + 1}
                expanded={expanded}
                toggle={toggle}
                selectedPath={selectedPath}
                onSelect={onSelect}
              />
            )}
          </div>
        )
      })}
    </>
  )
}

/**
 * ArtifactExplorer — a codebase browser for the project workspace. LEFT: a collapsible
 * FOLDER TREE built from the generated files (filtered to `category` when given). RIGHT:
 * the selected file's contents in a mono viewer, with a Run button for runnable files
 * (.py/.js) that executes them in the guarded backend runner and shows captured output.
 * Empty state when the workspace has no files yet. Polls every 10s via useArtifacts.
 */
export function ArtifactExplorer({ category, title }: ArtifactExplorerProps) {
  const { data: artifacts } = useArtifacts()
  const [selectedPath, setSelectedPath] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const run = useRunProgram()

  const items = useMemo(() => {
    const all = artifacts ?? []
    return category ? all.filter((a) => a.category === category) : all
  }, [artifacts, category])

  const tree = useMemo(() => buildTree(items), [items])
  // Default: every folder expanded; `collapsed` holds the ones the user closed.
  const expanded = useMemo(() => {
    const all = allFolderPaths(tree)
    collapsed.forEach((p) => all.delete(p))
    return all
  }, [tree, collapsed])

  const toggle = (path: string) =>
    setCollapsed((cur) => {
      const next = new Set(cur)
      next.has(path) ? next.delete(path) : next.add(path)
      return next
    })

  const onSelect = (path: string) => {
    setSelectedPath(path)
    run.reset() // clear stale run output when switching files
  }

  const { data: content, isFetching } = useArtifact(selectedPath)
  const selectedArtifact = items.find((a) => a.path === selectedPath)
  const runnable = selectedPath ? isRunnable(selectedPath) : false
  const result = run.data

  return (
    <GlassCard padding="none" className="overflow-hidden">
      <div className="border-b border-white/5 p-5">
        <SectionHeader label={title} count={items.length} />
      </div>

      {items.length === 0 ? (
        <EmptyState
          icon={Folder}
          title="No files yet"
          hint="Assign a task to the CEO — each agent's generated file lands here, browsable as a codebase."
          className="py-16"
        />
      ) : (
        <div className="grid min-h-[28rem] grid-cols-1 lg:grid-cols-[20rem_1fr]">
          {/* LEFT: folder tree */}
          <ScrollArea className="max-h-[40rem] border-b border-white/5 lg:border-b-0 lg:border-r">
            <div className="flex flex-col gap-0.5 p-2">
              <TreeRows node={tree} depth={0} expanded={expanded} toggle={toggle} selectedPath={selectedPath} onSelect={onSelect} />
            </div>
          </ScrollArea>

          {/* RIGHT: code viewer + run */}
          <div className="flex min-w-0 flex-col">
            {selectedPath ? (
              <>
                <div className="flex items-center gap-2 border-b border-white/5 px-4 py-2.5">
                  <FileText className="h-4 w-4 shrink-0 text-omnivra-cyan" aria-hidden />
                  <span className="min-w-0 flex-1 truncate font-mono text-xs text-[#a1a1aa]">{selectedPath}</span>
                  {selectedArtifact && (
                    <span className="shrink-0 text-[10px] text-[#52525b]">{formatModified(selectedArtifact.modified)}</span>
                  )}
                  {runnable && (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={run.isPending}
                      onClick={() => run.mutate(selectedPath)}
                      className="shrink-0 hover:text-omnivra-emerald"
                    >
                      {run.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Play className="h-3.5 w-3.5" aria-hidden />}
                      {run.isPending ? 'Running…' : 'Run'}
                    </Button>
                  )}
                </div>

                <ScrollArea className="max-h-[24rem] flex-1">
                  <pre className="whitespace-pre-wrap break-words p-4 font-mono text-xs leading-relaxed text-[#e4e4e7]">
                    {content?.content ?? (isFetching ? 'Loading…' : '')}
                  </pre>
                </ScrollArea>

                {/* Run output panel */}
                {(run.isPending || result || run.isError) && (
                  <div className="border-t border-white/[0.08] bg-black/30">
                    <div className="flex items-center gap-2 px-4 py-2 text-[11px]">
                      <Terminal className="h-3.5 w-3.5 text-omnivra-cyan" aria-hidden />
                      <span className="font-medium text-[#d4d4d8]">Output</span>
                      {result && (
                        <NeonBadge tone={result.ok ? 'success' : result.timedOut ? 'warning' : 'danger'} dot>
                          {result.timedOut ? 'timed out' : result.ok ? 'ok' : `exit ${result.exitCode ?? '—'}`}
                        </NeonBadge>
                      )}
                      {result && <span className="text-[#52525b]">{result.command} · {result.durationMs}ms</span>}
                    </div>
                    <ScrollArea className="max-h-[14rem]">
                      <pre className="whitespace-pre-wrap break-words px-4 pb-4 font-mono text-[11px] leading-relaxed">
                        {run.isPending && <span className="text-[#71717a]">Running in the guarded workspace runner…</span>}
                        {run.isError && <span className="text-omnivra-pink">Could not reach the runner. Try again.</span>}
                        {result && (
                          <>
                            {result.stdout && <span className="text-[#d4d4d8]">{result.stdout}</span>}
                            {result.stderr && <span className="text-omnivra-pink">{result.stdout ? '\n' : ''}{result.stderr}</span>}
                            {!result.stdout && !result.stderr && <span className="text-[#71717a]">{result.note || '(no output)'}</span>}
                          </>
                        )}
                      </pre>
                    </ScrollArea>
                  </div>
                )}
              </>
            ) : (
              <EmptyState
                icon={FileText}
                title="Select a file"
                hint="Pick a file in the tree to view it. Runnable files (.py / .js) get a Run button."
                className="my-auto"
              />
            )}
          </div>
        </div>
      )}
    </GlassCard>
  )
}
