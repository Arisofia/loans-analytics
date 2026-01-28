/* eslint-disable no-console */
/** Repository layout helper for ABACO with optional strict and JSON modes. */
// Node.js compatible version
import fs from 'node:fs'
import path from 'node:path'
interface CheckTarget {
  label: string
  path: string
}
interface PathInsight extends CheckTarget {
  exists: boolean
  type: 'directory' | 'file' | 'other'
  modified?: string
}
const repoRoot = path.resolve(process.cwd())
function normalizeUserPath(userPath: string): string {
  if (!userPath) {
    throw new Error('Path argument is empty')
  }
  // Reject absolute paths
  if (path.isAbsolute(userPath)) {
    throw new Error('Absolute paths are not allowed')
  }
  // Reject any ../ or .. segments (path traversal)
  if (userPath.includes('..') || userPath.split(path.sep).includes('..')) {
    throw new Error('Path contains parent directory traversal (..)')
  }
  // Reject unsafe characters (basic set)
  if (/[~*?<>|"\r\n]/.test(userPath)) {
    throw new Error('Path contains unsafe characters')
  }
  // Always resolve against a fixed base and verify
  const resolved = path.resolve(repoRoot, userPath)
  const relative = path.relative(repoRoot, resolved)
  if (relative === '..' || relative.startsWith('..' + path.sep)) {
    throw new Error('Path escapes the repository root')
  }
  return resolved
}
const defaultAreas: CheckTarget[] = [
  { label: 'Web dashboard', path: 'apps/web' },
  { label: 'Analytics pipelines', path: 'apps/analytics' },
  { label: 'Infrastructure automation', path: 'infra/azure' },
  { label: 'Documentation', path: 'docs' },
  { label: 'Data samples', path: 'data_samples' },
]
const normalizedDefaultAreas = defaultAreas.map((target) => ({
  ...target,
  path: normalizeUserPath(target.path),
}))
const args = process.argv.slice(2)
const { strict, json, extras } = parseArgs(args)
const keyAreas = [...normalizedDefaultAreas, ...extras]
function parseArgs(args: string[]) {
  const options = {
    strict: false,
    json: false,
    extras: [] as CheckTarget[],
  }
  for (const arg of args) {
    if (arg === '--strict') options.strict = true
    else if (arg === '--json') options.json = true
    else if (arg.startsWith('--path=')) {
      const descriptor = arg.slice('--path='.length)
      const [label, extraPath] = descriptor.includes(':')
        ? descriptor.split(':', 2)
        : [descriptor, descriptor]
      if (extraPath) {
        try {
          const normalized = normalizeUserPath(extraPath)
          options.extras.push({ label, path: normalized })
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'invalid path argument'
          console.error(`Invalid --path value "${extraPath}": ${message}`)
          process.exit(1)
        }
      }
    }
  }
  return options
}
function describePathSync(target: CheckTarget): PathInsight {
  try {
    const stats = fs.lstatSync(target.path)
    const type = stats.isDirectory()
      ? 'directory'
      : stats.isFile()
        ? 'file'
        : 'other'
    return {
      ...target,
      exists: true,
      type,
      modified: stats.mtime ? stats.mtime.toISOString() : undefined,
    }
  } catch {
    return { ...target, exists: false, type: 'other' }
  }
}
const results = keyAreas.map(describePathSync)
if (json) {
  console.log(JSON.stringify(results, null, 2))
} else {
  for (const entry of results) {
    const status = entry.exists ? 'OK' : 'MISSING'
    console.log(
      `[${status}] ${entry.label} -> ${entry.path} (${entry.type}${
        entry.modified ? `, modified=${entry.modified}` : ''
      })`
    )
  }
}
if (strict && results.some((entry) => !entry.exists)) process.exit(1)
export {} // Make this file a module to allow top-level await
