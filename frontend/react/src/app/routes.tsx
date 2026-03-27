import { createBrowserRouter } from "react-router";
import { RootLayout } from "./components/layout/RootLayout";
import { HomePage } from "./pages/HomePage";
import { PortfolioOverview } from "./pages/PortfolioOverview";
import { ExecutiveCommandCenter } from "./pages/ExecutiveCommandCenter";
import { RiskIntelligence } from "./pages/RiskIntelligence";
import { CollectionsOperations } from "./pages/CollectionsOperations";
import { TreasuryLiquidity } from "./pages/TreasuryLiquidity";
import { SalesGrowth } from "./pages/SalesGrowth";
import { VintageAnalysis } from "./pages/VintageAnalysis";
import { UnitEconomics } from "./pages/UnitEconomics";
import { CovenantCompliance } from "./pages/CovenantCompliance";
import { NotFound } from "./pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: HomePage },
      { path: "portfolio", Component: PortfolioOverview },
      { path: "executive", Component: ExecutiveCommandCenter },
      { path: "risk", Component: RiskIntelligence },
      { path: "collections", Component: CollectionsOperations },
      { path: "treasury", Component: TreasuryLiquidity },
      { path: "sales", Component: SalesGrowth },
      { path: "vintage", Component: VintageAnalysis },
      { path: "unit-economics", Component: UnitEconomics },
      { path: "covenants", Component: CovenantCompliance },
      { path: "*", Component: NotFound },
    ],
  },
]);
