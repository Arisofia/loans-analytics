/** Repository layout helper for ABACO with optional strict and JSON modes. */
// Node.js compatible version
import fs from 'fs'
import path from 'path'
interface CheckTarget {
  label: string
  path: string
}

interface PathInsight extends CheckTarget {
  exists: boolean
  type: 'directory' | 'file' | 'other'
  modified?: string
}

const repoName = 'abaco-loans-analytics'
const repoRoot = path.resolve(process.cwd())

function normalizeUserPath(userPath: string): string {
  if (!userPath) {
    throw new Error('Path argument is empty')
  }
  if (path.isAbsolute(userPath)) {
    throw new Error('Absolute paths are not allowed')
  }
  // Reject any path segments with .., /, \, or unsafe chars
  if (userPath.includes('..') || userPath.includes('/') || userPath.includes('\\')) {
    throw new Error('Path contains forbidden segments')
  }
  // Optionally, allowlist known safe paths (example: only allow certain folders/files)
  // const allowed = ['apps/web', 'apps/analytics', 'infra/azure', 'docs', 'data_samples']
  // if (!allowed.some((prefix) => userPath.startsWith(prefix))) {
  //   throw new Error('Path not in allowlist')
  // }
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
          const message = error instanceof Error ? error.message : 'invalid path argument'
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

function printHumanReadable(statuses: PathInsight[]) {
  console.log(`${repoName} — Deno helper`)
  console.log(
    'Check key folders before running Fitten, tests or deployments.\n'
  )

  for (const status of statuses) {
    const icon = status.exists ? '✅' : '⚠️'
    const detail = status.exists
      ? `${status.type}, last modified: ${status.modified ?? 'unknown'}`
      : 'missing – consider creating or syncing this path.'
    console.log(`• ${icon} ${status.label}: ${status.path} (${detail})`)
  }

  const missing = statuses.filter((entry) => !entry.exists)
  console.log(
    `\nSummary: ${statuses.length - missing.length}/${statuses.length} paths available.`
  )
  if (missing.length) {
    console.log('Missing paths:')
    for (const entry of missing)
      console.log(`  - ${entry.label} → ${entry.path}`)
    console.log(
      'Use --strict to exit with a non-zero code when required folders are absent.'
    )
  }

  console.log(
    '\nOptions:\n  --strict  Exit with code 1 if any path is missing\n  --json    Emit machine-readable JSON\n  --path=label:path  Check an additional path with a custom label'
  )
  console.log(
    '\nExample:\n  deno run --allow-read main.ts --strict --path=Temp:data_samples/tmp'
  )
}

const results = keyAreas.map(describePathSync)

if (json) console.log(JSON.stringify(results, null, 2))
else printHumanReadable(results)

if (strict && results.some((entry) => !entry.exists)) process.exit(1)

export {} // Make this file a module to allow top-level await

export {} // Make this file a module to allow top-level await
