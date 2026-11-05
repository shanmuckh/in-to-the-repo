"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { userHistoryRoute } from "@/utils/APIRoutes";
import { getAuthHeaders, isAuthenticated } from "@/utils/auth";
import { GridBackground } from "@/components/GridBackground";
import Link from "next/link";

interface HistoryEntry {
  id: number;
  repo_url: string;
  branch: string;
  analyzed_at: string;
  notes: string | null;
  repo_analysis_id?: number;
}

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    async function fetchHistory() {
      try {
        const response = await axios.get(userHistoryRoute, {
          headers: getAuthHeaders(),
        });
        const historyData = response.data.history || [];
        setHistory(historyData);
      } catch (err) {
        console.error("Failed to fetch history:", err);
        setError("Failed to load analysis history");
      } finally {
        setLoading(false);
      }
    }

    fetchHistory();
  }, [router]);

  const handleViewAnalysis = async (entry: HistoryEntry) => {
    if (!entry.repo_analysis_id) {
      console.error("No repo_analysis_id found for entry");
      setError("Cannot load this analysis");
      return;
    }

    router.push(`/analyze?id=${entry.repo_analysis_id}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <GridBackground />
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <GridBackground />
      <div className="relative z-10 container mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold">Analysis History</h1>
          <Link
            href="/"
            className="px-4 py-2 rounded-md bg-neutral-800 hover:bg-neutral-700 transition-colors"
          >
            Back to Home
          </Link>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-3 rounded mb-8">
            {error}
          </div>
        )}

        {history.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-neutral-400 text-lg mb-4">
              No analysis history yet
            </p>
            <Link
              href="/"
              className="inline-block px-6 py-3 rounded-full bg-neutral-800 hover:bg-neutral-700 transition-colors"
            >
              Analyze your first repository
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {history.map((entry) => {
              console.log("[HISTORY] Rendering entry:", entry);
              return (
              <div
                key={entry.id}
                className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 hover:border-neutral-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {entry.repo_url}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-neutral-400">
                      <span>Branch: {entry.branch}</span>
                      <span>•</span>
                      <span>
                        {new Date(entry.analyzed_at).toLocaleDateString(
                          "en-US",
                          {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          }
                        )}
                      </span>
                    </div>
                    {entry.notes && (
                      <p className="mt-3 text-neutral-300">{entry.notes}</p>
                    )}
                  </div>
                  <div className="ml-4 flex gap-2">
                    <button
                      onClick={() => handleViewAnalysis(entry)}
                      className="px-4 py-2 rounded-md bg-purple-600 hover:bg-purple-700 transition-colors whitespace-nowrap"
                    >
                      View Analysis
                    </button>
                    <button
                      onClick={() => {
                        console.log("[HISTORY] Redirecting to home to re-analyze");
                        window.location.href = `/?repo=${encodeURIComponent(
                          entry.repo_url
                        )}&branch=${encodeURIComponent(entry.branch)}`;
                      }}
                      className="px-4 py-2 rounded-md bg-neutral-800 hover:bg-neutral-700 transition-colors whitespace-nowrap"
                    >
                      Re-analyze
                    </button>
                  </div>
                </div>
              </div>
            )})}
          </div>
        )}
      </div>
    </div>
  );
}
