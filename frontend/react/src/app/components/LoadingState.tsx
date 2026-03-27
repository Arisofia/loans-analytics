interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading data from Supabase..." }: LoadingStateProps) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div
          className="w-12 h-12 rounded-full border-4 border-t-transparent mx-auto mb-4 animate-spin"
          style={{ borderColor: "var(--primary-purple)", borderTopColor: "transparent" }}
        />
        <p className="text-sm" style={{ color: "var(--medium-gray)" }}>{message}</p>
      </div>
    </div>
  );
}

interface ErrorStateProps {
  error?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ error, message, onRetry }: ErrorStateProps) {
  const displayError = error ?? message ?? "Unknown error";
  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div
        className="max-w-md w-full rounded-lg p-6 border"
        style={{ backgroundColor: "var(--dark-blue)", borderColor: "var(--error)" }}
      >
        <p className="text-sm font-semibold mb-2" style={{ color: "var(--error)" }}>
          ⚠ Failed to load data
        </p>
        <p className="text-xs mb-4" style={{ color: "var(--medium-gray)" }}>{displayError}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 rounded text-sm font-semibold"
            style={{ background: "var(--gradient-title)", color: "var(--bg-main)" }}
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
