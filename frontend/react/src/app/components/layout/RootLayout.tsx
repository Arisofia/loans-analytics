import { Outlet, Link, useLocation } from "react-router";
import { useState } from "react";
import { 
  Home, 
  BarChart3, 
  TrendingUp, 
  AlertTriangle,
  DollarSign,
  Users,
  Menu,
  X,
  Settings,
  PieChart,
  Shield,
  Percent,
  Activity,
  Brain
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navigation = [
  {
    title: "OPERATIONAL",
    items: [
      { name: "Home",                   path: "/",              icon: Home },
      { name: "Executive Command Center",path: "/executive",    icon: BarChart3 },
      { name: "Portfolio Overview",      path: "/portfolio",    icon: TrendingUp },
      { name: "Collections Operations",  path: "/collections",  icon: Users },
    ],
  },
  {
    title: "ANALYTICS",
    items: [
      { name: "Risk Intelligence", path: "/risk", icon: AlertTriangle },
      { name: "Vintage & Cohort", path: "/vintage", icon: Activity },
      { name: "Risk Intelligence",       path: "/risk",         icon: AlertTriangle },
      { name: "Vintage & Cohort",        path: "/vintage",      icon: Activity },
    ],
  },
  {
    title: "FINANCIAL",
    items: [
      { name: "Treasury & Liquidity",    path: "/treasury",     icon: DollarSign },
      { name: "Unit Economics",          path: "/unit-economics",icon: Percent },
      { name: "Covenant Compliance",     path: "/covenants",    icon: Shield },
    ],
  },
  {
    title: "GROWTH",
    items: [
      { name: "Sales & Growth", path: "/sales", icon: PieChart },
      { name: "Marketing Intelligence", path: "/marketing", icon: TrendingUp },
      { name: "Sales & Growth",          path: "/sales",        icon: PieChart },
      { name: "Marketing Intelligence",  path: "/marketing",    icon: TrendingUp },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      { name: "Investor Room",           path: "/investor-room",icon: Shield },
      { name: "AI Decision Center",      path: "/ai-center",    icon: Brain },
    ],
  },
];

export function RootLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen">
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 border-b flex items-center justify-between px-4 z-40"
           style={{ 
             backgroundColor: 'var(--dark-blue)',
             borderColor: 'var(--purple-dark)'
           }}>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-white"
          >
            {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </Button>
          <h1 className="text-xl font-bold" style={{ 
            background: 'var(--gradient-title)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Commercial/Financials analytics
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="text-white">
            <Settings className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Desktop Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-screen w-64 border-r transition-transform duration-300 z-50
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
        style={{ 
          backgroundColor: 'var(--dark-blue)',
          borderColor: 'var(--purple-dark)'
        }}
      >
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="h-16 flex items-center justify-center border-b px-4"
               style={{ borderColor: 'var(--purple-dark)' }}>
            <h1 className="text-sm font-bold text-center leading-tight" style={{ 
              background: 'var(--gradient-title)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Commercial/<br />Financials analytics
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-6">
            {navigation.map((section) => (
              <div key={section.title}>
                <h3 className="text-xs uppercase tracking-wider mb-2 px-3"
                    style={{ color: 'var(--medium-gray)' }}>
                  {section.title}
                </h3>
                <ul className="space-y-1">
                  {section.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    return (
                      <li key={item.path}>
                        <Link
                          to={item.path}
                          className={`
                            flex items-center gap-3 px-3 py-2 rounded-lg transition-all
                            ${isActive
                              ? 'text-white font-semibold bg-[var(--sidebar-accent)]'
                              : 'hover:bg-opacity-10 hover:bg-white text-[var(--light-gray)]'
                            }
                          `}
                        >
                          <Icon className="h-5 w-5" />
                          <span className="text-sm">{item.name}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>

          {/* User Section */}
          <div className="p-4 border-t" style={{ borderColor: 'var(--purple-dark)' }}>
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 rounded-full flex items-center justify-center"
                   style={{ backgroundColor: 'var(--primary-purple)' }}>
                <span className="text-sm font-semibold" style={{ color: 'var(--bg-main)' }}>
                  U
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold" style={{ color: 'var(--white)' }}>
                  Usuario
                </p>
                <p className="text-xs" style={{ color: 'var(--medium-gray)' }}>
                  Admin
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="md:ml-64 pt-16 md:pt-0 min-h-screen" style={{ backgroundColor: 'var(--bg-main)' }}>
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 border-t flex items-center justify-around z-40"
           style={{ 
             backgroundColor: 'var(--dark-blue)',
             borderColor: 'var(--purple-dark)'
           }}>
        <Link to="/" className="flex flex-col items-center gap-1">
          <Home className="h-5 w-5" style={{ color: location.pathname === '/' ? 'var(--primary-purple)' : 'var(--medium-gray)' }} />
          <span className="text-xs" style={{ color: location.pathname === '/' ? 'var(--primary-purple)' : 'var(--medium-gray)' }}>
            Home
          </span>
        </Link>
        <Link to="/portfolio" className="flex flex-col items-center gap-1">
          <BarChart3 className="h-5 w-5" style={{ color: location.pathname === '/portfolio' ? 'var(--primary-purple)' : 'var(--medium-gray)' }} />
          <span className="text-xs" style={{ color: location.pathname === '/portfolio' ? 'var(--primary-purple)' : 'var(--medium-gray)' }}>
            Portfolio
          </span>
        </Link>
        <Link to="/risk" className="flex flex-col items-center gap-1">
          <AlertTriangle className="h-5 w-5" style={{ color: location.pathname === '/risk' ? 'var(--primary-purple)' : 'var(--medium-gray)' }} />
          <span className="text-xs" style={{ color: location.pathname === '/risk' ? 'var(--primary-purple)' : 'var(--medium-gray)' }}>
            Alerts
          </span>
        </Link>
        <Link to="/executive" className="flex flex-col items-center gap-1">
          <TrendingUp className="h-5 w-5" style={{ color: location.pathname === '/executive' ? 'var(--primary-purple)' : 'var(--medium-gray)' }} />
          <span className="text-xs" style={{ color: location.pathname === '/executive' ? 'var(--primary-purple)' : 'var(--medium-gray)' }}>
            AI
          </span>
        </Link>
      </nav>
    </div>
  );
}
