/* eslint-disable no-console */
/** Repository layout helper for ABACO with optional strict and JSON modes. */
// Node.js compatible version
import fs from "node:fs";
import path from "node:path";
interface CheckTarget {
  label: string;
  path: string;
}
interface PathInsight extends CheckTarget {
  exists: boolean;
  type: "directory" | "file" | "other";
  modified?: string;
}
const repoRoot = path.resolve(process.cwd());
function normalizeUserPath(userPath: string): string {
  if (!userPath) {
    throw new Error("Path argument is empty");
  }
  // Reject absolute paths
  if (path.isAbsolute(userPath)) {
    throw new Error("Absolute paths are not allowed");
  }
  // Reject any ../ or .. segments (path traversal)
  if (userPath.includes("..") || userPath.split(path.sep).includes("..")) {
    throw new Error("Path contains parent directory traversal (..)");
  }
  // Reject unsafe characters (basic set)
  if (/[~*?<>|"\r\n]/.test(userPath)) {
    throw new Error("Path contains unsafe characters");
  }
  // Always resolve against a fixed base and verify
  const resolved = path.resolve(repoRoot, userPath);
  const relative = path.relative(repoRoot, resolved);
  if (relative === ".." || relative.startsWith(".." + path.sep)) {
    throw new Error("Path escapes the repository root");
  }
  return resolved;
}
const defaultAreas: CheckTarget[] = [
  { label: "Analytics pipelines", path: "python/apps/analytics" },
  { label: "Infrastructure automation", path: "infra/azure" },
  { label: "Documentation", path: "docs" },
  { label: "Data", path: "data" },
];
const normalizedDefaultAreas = defaultAreas.map((target) => ({
  ...target,
  path: normalizeUserPath(target.path),
}));
const args = process.argv.slice(2);
const { strict, json, extras } = parseArgs(args);
const keyAreas = [...normalizedDefaultAreas, ...extras];

interface ParsedArgs {
  strict: boolean;
  json: boolean;
  extras: CheckTarget[];
}

function parsePathDescriptor(descriptor: string): [string, string] {
  return descriptor.includes(":")
    ? (descriptor.split(":", 2) as [string, string])
    : [descriptor, descriptor];
}

function handlePathArgument(descriptor: string, options: ParsedArgs): void {
  const [label, extraPath] = parsePathDescriptor(descriptor);

  if (!extraPath) {
    return;
  }

  try {
    const normalized = normalizeUserPath(extraPath);
    options.extras.push({ label, path: normalized });
  } catch (error) {
    const message = error instanceof Error
      ? error.message
      : "invalid path argument";
    console.error(`Invalid --path value "${extraPath}": ${message}`);
    process.exit(1);
  }
}

function processArgument(arg: string, options: ParsedArgs): void {
  if (arg === "--strict") {
    options.strict = true;
    return;
  }

  if (arg === "--json") {
    options.json = true;
    return;
  }

  if (arg.startsWith("--path=")) {
    const descriptor = arg.slice("--path=".length);
    handlePathArgument(descriptor, options);
  }
}

function parseArgs(args: string[]): ParsedArgs {
  const options: ParsedArgs = {
    strict: false,
    json: false,
    extras: [],
  };

  args.forEach((arg) => processArgument(arg, options));

  return options;
}

function determinePathType(stats: fs.Stats): "directory" | "file" | "other" {
  if (stats.isDirectory()) return "directory";
  if (stats.isFile()) return "file";
  return "other";
}

function createPathInsight(target: CheckTarget, stats: fs.Stats): PathInsight {
  return {
    ...target,
    exists: true,
    type: determinePathType(stats),
    modified: stats.mtime ? stats.mtime.toISOString() : undefined,
  };
}

function createMissingPathInsight(target: CheckTarget): PathInsight {
  return { ...target, exists: false, type: "other" };
}

function describePathSync(target: CheckTarget): PathInsight {
  try {
    const stats = fs.lstatSync(target.path);
    return createPathInsight(target, stats);
  } catch {
    return createMissingPathInsight(target);
  }
}

function formatEntryDetails(entry: PathInsight): string {
  const modifiedInfo = entry.modified ? `, modified=${entry.modified}` : "";
  return `${entry.type}${modifiedInfo}`;
}

function formatEntryOutput(entry: PathInsight): string {
  const status = entry.exists ? "OK" : "MISSING";
  const details = formatEntryDetails(entry);
  return `[${status}] ${entry.label} -> ${entry.path} (${details})`;
}

function outputResults(results: PathInsight[], json: boolean): void {
  if (json) {
    console.log(JSON.stringify(results, null, 2));
    return;
  }

  results.forEach((entry) => {
    console.log(formatEntryOutput(entry));
  });
}

function checkStrictMode(results: PathInsight[], strict: boolean): void {
  if (strict && results.some((entry) => !entry.exists)) {
    process.exit(1);
  }
}

const results = keyAreas.map((area) => describePathSync(area));
outputResults(results, json);
checkStrictMode(results, strict);
export {}; // Make this file a module to allow top-level await
