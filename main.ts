/** Simple Deno helper that reports the repository layout before launching other helpers. */
const repoName = "abaco-loans-analytics";
const keyAreas = [
  { label: "Web dashboard", path: "apps/web" },
  { label: "Analytics pipelines", path: "apps/analytics" },
  { label: "Infrastructure automation", path: "infra/azure" },
  { label: "Documentation", path: "docs" },
  { label: "Data samples", path: "data_samples" },
];

async function describePath(path: string) {
  try {
    const stats = await Deno.lstat(path);
    const type = stats.isDirectory ? "directory" : "file";
    console.log(`• ${path} (${type}) exists, last modified: ${stats.mtime?.toISOString() ?? "unknown"}`);
  } catch {
    console.log(`• ${path} (missing) – consider creating it or checking the repo structure.`);
  }
}

console.log(`${repoName} — Deno helper`);
console.log("Check that the key folders exist before running fitten, tests or deployments:\n");

for (const area of keyAreas) {
  console.log(`${area.label}: ${area.path}`);
  await describePath(area.path);
}

console.log("\nTo run the Fitten Code AI onboarding helper, first make sure your model path is configured (see docs/Fitten-Code-AI-Manual.md), then use:\n");
console.log("  deno run --allow-all main.ts");
