/** Repository layout helper for ABACO with optional strict and JSON modes. */
interface CheckTarget {
  label: string;
  path: string;
}

interface PathInsight extends CheckTarget {
  exists: boolean;
  type: "directory" | "file" | "other";
  modified?: string;
}

const repoName = "abaco-loans-analytics";
const defaultAreas: CheckTarget[] = [
  { label: "Web dashboard", path: "apps/web" },
  { label: "Analytics pipelines", path: "apps/analytics" },
  { label: "Infrastructure automation", path: "infra/azure" },
  { label: "Documentation", path: "docs" },
  { label: "Data samples", path: "data_samples" },
];

const { strict, json, extras } = parseArgs(Deno.args);
const keyAreas = [...defaultAreas, ...extras];

function parseArgs(args: string[]) {
  const options = {
    strict: false,
    json: false,
    extras: [] as CheckTarget[],
  };

  for (const arg of args) {
    if (arg === "--strict") options.strict = true;
    else if (arg === "--json") options.json = true;
    else if (arg.startsWith("--path=")) {
      const descriptor = arg.slice("--path=".length);
      const [label, path] = descriptor.includes(":")
        ? descriptor.split(":", 2)
        : [descriptor, descriptor];
      if (path) options.extras.push({ label, path });
    }
  }

  return options;
}

async function describePath(target: CheckTarget): Promise<PathInsight> {
  try {
    const stats = await Deno.lstat(target.path);
    const type = stats.isDirectory
      ? "directory"
      : stats.isFile
        ? "file"
        : "other";

    return {
      ...target,
      exists: true,
      type,
      modified: stats.mtime?.toISOString(),
    };
  } catch {
    return { ...target, exists: false, type: "other" };
  }
}

function printHumanReadable(statuses: PathInsight[]) {
  console.log(`${repoName} — Deno helper`);
  console.log("Check key folders before running Fitten, tests or deployments.\n");

  for (const status of statuses) {
    const icon = status.exists ? "✅" : "⚠️";
    const detail = status.exists
      ? `${status.type}, last modified: ${status.modified ?? "unknown"}`
      : "missing – consider creating or syncing this path.";
    console.log(`• ${icon} ${status.label}: ${status.path} (${detail})`);
  }

  const missing = statuses.filter((entry) => !entry.exists);
  console.log(
    `\nSummary: ${statuses.length - missing.length}/${statuses.length} paths available.`,
  );
  if (missing.length) {
    console.log("Missing paths:");
    for (const entry of missing) console.log(`  - ${entry.label} → ${entry.path}`);
    console.log(
      "Use --strict to exit with a non-zero code when required folders are absent.",
    );
  }

  console.log("\nOptions:\n  --strict  Exit with code 1 if any path is missing\n  --json    Emit machine-readable JSON\n  --path=label:path  Check an additional path with a custom label");
  console.log("\nExample:\n  deno run --allow-read main.ts --strict --path=Temp:data_samples/tmp");
}

const results = [] as PathInsight[];
for (const area of keyAreas) results.push(await describePath(area));

if (json) console.log(JSON.stringify(results, null, 2));
else printHumanReadable(results);

if (strict && results.some((entry) => !entry.exists)) Deno.exit(1);
