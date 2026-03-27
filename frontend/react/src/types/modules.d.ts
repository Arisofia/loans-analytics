/* ------------------------------------------------------------------ *
 * Ambient module declarations — stubs so VS Code resolves imports    *
 * before `npm install`.  Remove this file after running npm install. *
 * ------------------------------------------------------------------ */

declare module "react" {
  export function useMemo<T>(factory: () => T, deps: readonly unknown[]): T;
  export function useState<T>(init: T | (() => T)): [T, (v: T | ((p: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void;
  export function useCallback<T extends (...args: any[]) => any>(cb: T, deps: readonly unknown[]): T;
  export function createContext<T>(defaultValue: T): any;
  export function useContext<T>(ctx: any): T;
  export const Fragment: any;
  export type ReactNode = any;
  export type FC<P = {}> = (props: P) => any;
  export type Key = string | number;
  export interface Attributes { key?: Key | null | undefined; }
  const React: any;
  export default React;
}

declare namespace JSX {
  interface Element {}
  interface ElementAttributesProperty { props: {}; }
  interface ElementChildrenAttribute { children: {}; }
  interface IntrinsicElements {
    [elemName: string]: any;
  }
  interface IntrinsicAttributes {
    key?: string | number | null | undefined;
  }
}

declare module "react/jsx-runtime" {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module "react-dom/client" {
  export function createRoot(container: Element | null): { render(el: any): void };
}

declare module "recharts" {
  export const LineChart: any;
  export const Line: any;
  export const AreaChart: any;
  export const Area: any;
  export const BarChart: any;
  export const Bar: any;
  export const PieChart: any;
  export const Pie: any;
  export const Cell: any;
  export const XAxis: any;
  export const YAxis: any;
  export const CartesianGrid: any;
  export const Tooltip: any;
  export const Legend: any;
  export const ResponsiveContainer: any;
}

declare module "react-router" {
  export function createBrowserRouter(routes: any[]): any;
  export function RouterProvider(props: { router: any }): any;
  export function Outlet(): any;
  export function Link(props: { to: string; className?: string; children?: any }): any;
  export function useLocation(): { pathname: string };
  export function useNavigate(): (to: string) => void;
}

declare module "lucide-react" {
  export type LucideIcon = any;
  export const Activity: any;
  export const AlertTriangle: any;
  export const ArrowDown: any;
  export const ArrowRight: any;
  export const ArrowUp: any;
  export const BarChart3: any;
  export const BookOpen: any;
  export const Brain: any;
  export const Building2: any;
  export const CheckCircle: any;
  export const CheckCircle2: any;
  export const ChevronDown: any;
  export const ChevronRight: any;
  export const Clock: any;
  export const CreditCard: any;
  export const DollarSign: any;
  export const Eye: any;
  export const FileText: any;
  export const Filter: any;
  export const Home: any;
  export const Layers: any;
  export const LineChart: any;
  export const Loader2: any;
  export const Menu: any;
  export const Percent: any;
  export const Phone: any;
  export const PieChart: any;
  export const RefreshCw: any;
  export const Scale: any;
  export const Send: any;
  export const Settings: any;
  export const Shield: any;
  export const ShieldAlert: any;
  export const Target: any;
  export const TrendingDown: any;
  export const TrendingUp: any;
  export const Users: any;
  export const Wallet: any;
  export const X: any;
  export const XCircle: any;
  export const Zap: any;
  const _default: any;
  export default _default;
}

declare module "@radix-ui/react-slot" {
  export const Slot: any;
}

declare module "class-variance-authority" {
  export function cva(base: string, config?: any): (...args: any[]) => string;
  export type VariantProps<T extends (...args: any[]) => any> = any;
}

declare module "clsx" {
  export type ClassValue = string | number | boolean | undefined | null | ClassValue[];
  export function clsx(...inputs: ClassValue[]): string;
}

/* ---- Deno / Supabase Edge Function JSR modules ---- */

declare module "jsr:@hono/hono" {
  export class Hono {
    constructor();
    basePath(path: string): Hono;
    use(path: string, ...middleware: any[]): void;
    get(path: string, handler: (c: any) => any): void;
    put(path: string, handler: (c: any) => any): void;
    post(path: string, handler: (c: any) => any): void;
  }
}

declare module "jsr:@hono/hono/cors" {
  export function cors(options?: Record<string, any>): any;
}

declare module "jsr:@hono/hono/logger" {
  export function logger(): any;
}

declare module "jsr:@supabase/supabase-js@2" {
  export function createClient(url: string, key: string): any;
}

declare module "tailwind-merge" {
  export function twMerge(...args: string[]): string;
}
