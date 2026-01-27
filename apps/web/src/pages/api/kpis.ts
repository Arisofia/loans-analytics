import type { NextApiRequest, NextApiResponse } from "next";
import fs from "fs";
import path from "path";

function readLatestKpiFile(kpiId: string): Record<string, unknown> | null {
  const baseDir =
    process.env.KPI_REPORTS_DIR ||
    path.join(process.cwd(), "..", "..", "..", "exports", "kpi_sets");
  const latestPath = path.join(baseDir, `${kpiId}_latest.json`);
  if (!fs.existsSync(latestPath)) {
    return null;
  }
  const raw = fs.readFileSync(latestPath, "utf-8");
  return JSON.parse(raw) as Record<string, unknown>;
}

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  const portfolio = readLatestKpiFile("portfolio_core");
  const growth = readLatestKpiFile("growth_core");

  if (!portfolio && !growth) {
    res.status(404).json({ error: "No KPI data available" });
    return;
  }

  res.status(200).json({
    portfolio,
    growth,
  });
}
