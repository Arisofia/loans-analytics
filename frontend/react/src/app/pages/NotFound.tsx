import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex items-center justify-center min-h-screen p-6">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold" style={{ color: 'var(--primary-purple)' }}>
          404
        </h1>
        <p className="text-xl" style={{ color: 'var(--white)' }}>
          Page not found
        </p>
        <p style={{ color: 'var(--medium-gray)' }}>
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/">
          <Button className="gap-2">
            <Home className="h-4 w-4" />
            Go Home
          </Button>
        </Link>
      </div>
    </div>
  );
}
