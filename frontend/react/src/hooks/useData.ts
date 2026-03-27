import { useState, useEffect } from "react";
import { fetchSection } from "../services/api";

export function useSection<T = unknown>(section: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchSection<T>(section)
      .then((d) => { setData(d); })
      .catch((e) => { setError(String(e)); })
      .finally(() => { setLoading(false); });
  };

  useEffect(() => {
    load();
  }, [section]);

  return { data, loading, error, refetch: load };
}
