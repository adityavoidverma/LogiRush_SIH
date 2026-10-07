// src/pages/EvaluationDashboard.jsx
// IR evaluation dashboard — real P@K, Recall@K, MRR, latency from live runs.

import { useState } from "react";
import { API_BASE_URL } from "../api/client";

const METHODS = ["tfidf", "bm25", "dense", "hybrid"];
const K_OPTIONS = [1, 3, 5, 10];

const METHOD_COLOR = {
  hybrid: "text-accent",
  bm25:   "text-blue-400",
  tfidf:  "text-yellow-400",
  dense:  "text-purple-400",
};

function MetricCell({ value }) {
  if (value === undefined || value === null) return <td className="px-4 py-2 text-ink-secondary">—</td>;
  const pct = Math.round(value * 100);
  const color = pct >= 60 ? "text-green-400" : pct >= 30 ? "text-yellow-400" : "text-red-400";
  return (
    <td className={`px-4 py-2 font-mono tabular-nums ${color}`}>
      {pct}%
    </td>
  );
}

function LatencyCell({ value }) {
  if (value === undefined || value === null) return <td className="px-4 py-2 text-ink-secondary">—</td>;
  const color = value < 50 ? "text-green-400" : value < 200 ? "text-yellow-400" : "text-red-400";
  return (
    <td className={`px-4 py-2 font-mono tabular-nums ${color}`}>
      {value.toFixed(1)} ms
    </td>
  );
}

export default function EvaluationDashboard() {
  const [k, setK]             = useState(5);
  const [loading, setLoading] = useState(false);
  const [data, setData]       = useState(null);
  const [error, setError]     = useState(null);
  const [expanded, setExpanded] = useState(null);

  const runEval = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/evaluation/results?method=all&k=${k}`);
      const json = await res.json();
      if (!res.ok) throw new Error(json.message || `Error ${res.status}`);
      setData(json);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const table = data?.comparison_table || [];

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-ink mb-2">IR Evaluation Dashboard</h1>
        <p className="text-ink-secondary">
          Compare TF-IDF, BM25, dense and hybrid retrieval on the judged query set.
          All metrics are measured from live runs — no fabricated numbers.
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2 text-sm text-ink-secondary">
          <label htmlFor="k-select">K =</label>
          <select
            id="k-select"
            value={k}
            onChange={(e) => setK(+e.target.value)}
            className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-sm"
          >
            {K_OPTIONS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <button
          onClick={runEval}
          disabled={loading}
          className="px-5 py-2 bg-accent rounded-lg font-semibold hover:brightness-110 disabled:opacity-50 transition-all text-sm"
          style={{ color: "var(--bg-contrast)" }}
        >
          {loading ? "Running…" : "Run Evaluation"}
        </button>
        {data && (
          <span className="text-xs text-ink-secondary">
            {data.details?.hybrid?.num_queries ?? "—"} queries evaluated
          </span>
        )}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-500/40 rounded-lg p-4 mb-6 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Comparison table */}
      {table.length > 0 && (
        <div className="mb-8 overflow-x-auto">
          <h2 className="text-sm font-semibold text-ink-secondary uppercase tracking-wider mb-3">
            Comparison @ K={k}
          </h2>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-ink-secondary text-left text-xs uppercase tracking-wider">
                <th className="px-4 py-2">Retriever</th>
                <th className="px-4 py-2">P@{k}</th>
                <th className="px-4 py-2">Recall@{k}</th>
                <th className="px-4 py-2">F1@{k}</th>
                <th className="px-4 py-2">MRR</th>
                <th className="px-4 py-2">Latency</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row) => (
                <tr key={row.method} className="border-b border-white/5 hover:bg-white/5">
                  <td className={`px-4 py-2 font-semibold ${METHOD_COLOR[row.method] || "text-ink"}`}>
                    {row.method.toUpperCase()}
                  </td>
                  <MetricCell value={row[`P@${k}`]} />
                  <MetricCell value={row[`Recall@${k}`]} />
                  <MetricCell value={row[`F1@${k}`]} />
                  <MetricCell value={row.MRR} />
                  <LatencyCell value={row.latency_ms} />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Per-query breakdown */}
      {data?.details?.hybrid?.per_query && (
        <div>
          <h2 className="text-sm font-semibold text-ink-secondary uppercase tracking-wider mb-3">
            Per-Query Details (Hybrid)
          </h2>
          <div className="space-y-2">
            {data.details.hybrid.per_query.map((q) => (
              <div key={q.query_id} className="bg-surface border border-white/10 rounded-lg overflow-hidden">
                <button
                  className="w-full text-left px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
                  onClick={() => setExpanded(expanded === q.query_id ? null : q.query_id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-ink-secondary">{q.query_id}</span>
                    <span className="text-sm text-ink">{q.query}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono shrink-0">
                    <span className={q.p_at_k >= 0.5 ? "text-green-400" : "text-red-400"}>
                      P@{k} {Math.round(q.p_at_k * 100)}%
                    </span>
                    <span className="text-ink-secondary">RR {q.rr.toFixed(2)}</span>
                    <span className="text-ink-secondary">{q.latency_ms.toFixed(0)}ms</span>
                    <span className="text-ink-secondary">{expanded === q.query_id ? "▲" : "▼"}</span>
                  </div>
                </button>

                {expanded === q.query_id && (
                  <div className="px-4 pb-3 text-xs text-ink-secondary border-t border-white/10 pt-3 space-y-1">
                    <p>
                      <span className="text-ink">Retrieved:</span>{" "}
                      {q.retrieved.join(", ") || "—"}
                    </p>
                    <p>
                      <span className="text-ink">Relevant:</span>{" "}
                      {q.relevant.join(", ")}
                    </p>
                    <div className="flex gap-4 pt-1">
                      <span>Recall@{k}: {Math.round(q.recall_at_k * 100)}%</span>
                      <span>F1@{k}: {Math.round(q.f1_at_k * 100)}%</span>
                      <span>RR: {q.rr.toFixed(3)}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
