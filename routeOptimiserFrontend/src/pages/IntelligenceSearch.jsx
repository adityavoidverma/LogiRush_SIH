// src/pages/IntelligenceSearch.jsx
// LogiRush: Pan-India Multi-Hazard Logistics Intelligence Search
// The primary IR demo page.

import { useState, useCallback, useRef } from "react";
import { API_BASE_URL } from "../api/client";

// ─── helpers ────────────────────────────────────────────────────────────────

const METHODS = [
  { value: "hybrid", label: "Hybrid (BM25 + Semantic + Freshness + Authority)" },
  { value: "bm25",   label: "BM25 only" },
  { value: "tfidf",  label: "TF-IDF only" },
  { value: "dense",  label: "Dense / Semantic only" },
];

const CARGO_TYPES = [
  { value: "",           label: "Any cargo" },
  { value: "medicine",   label: "Medicine" },
  { value: "relief",     label: "Relief Material" },
  { value: "food",       label: "Food" },
  { value: "perishable", label: "Perishable" },
  { value: "general",    label: "General" },
];

const EXAMPLE_QUERIES = [
  "Can I transport medicine from Guwahati to Kolkata today?",
  "flood risk in Assam NH27",
  "landslide risk near Sikkim highways",
  "safe route for relief material from Delhi to Guwahati",
  "cyclone impact on Odisha logistics",
  "heavy rainfall Kerala road disruption",
];

const RISK_COLORS = {
  CRITICAL: "text-red-500 border-red-500",
  HIGH:     "text-orange-400 border-orange-400",
  MEDIUM:   "text-yellow-400 border-yellow-400",
  LOW:      "text-green-400 border-green-400",
  UNKNOWN:  "text-gray-400 border-gray-400",
};

const SEV_BADGE = {
  critical: "bg-red-900/60 text-red-300",
  high:     "bg-orange-900/60 text-orange-300",
  medium:   "bg-yellow-900/60 text-yellow-300",
  low:      "bg-green-900/60 text-green-300",
};

const PROV_BADGE = {
  LIVE:      "bg-green-900/60 text-green-300",
  SAMPLED:   "bg-blue-900/60 text-blue-300",
  SYNTHETIC: "bg-gray-700 text-gray-300",
};

// ─── sub-components ─────────────────────────────────────────────────────────

function ScoreBar({ label, value, max = 1 }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-ink-secondary text-right shrink-0">{label}</span>
      <div className="flex-1 bg-white/10 rounded-full h-1.5">
        <div
          className="h-1.5 rounded-full bg-accent"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right text-ink font-mono">{value.toFixed(3)}</span>
    </div>
  );
}

function WhyPanel({ result, onClose }) {
  const doc = result;
  const scores = result.scores || {};
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-surface border border-white/20 rounded-xl p-6 max-w-lg w-full shadow-2xl">
        <div className="flex justify-between items-start mb-4">
          <h3 className="font-semibold text-ink">Why ranked #{result.rank}?</h3>
          <button onClick={onClose} className="text-ink-secondary hover:text-ink text-lg leading-none">✕</button>
        </div>

        <div className="space-y-2 mb-4">
          <ScoreBar label="BM25 relevance"      value={scores.bm25 ?? 0} />
          <ScoreBar label="TF-IDF"              value={scores.tfidf ?? 0} />
          <ScoreBar label="Semantic similarity" value={scores.semantic ?? 0} />
          <ScoreBar label="Freshness"           value={scores.freshness ?? 0} />
          <ScoreBar label="Geographic"          value={scores.geographic ?? 0} />
          <ScoreBar label="Source authority"    value={scores.authority ?? 0} />
          <div className="border-t border-white/10 pt-2">
            <ScoreBar label="Final score" value={result.final_score ?? 0} />
          </div>
        </div>

        <div className="text-xs text-ink-secondary space-y-1">
          <p><span className="text-ink">Source:</span> {doc.source} ({doc.source_type})</p>
          <p><span className="text-ink">Date:</span> {doc.date}</p>
          <p><span className="text-ink">Location:</span> {doc.location}</p>
          <p><span className="text-ink">Hazard:</span> {doc.hazard} — Severity: {doc.severity}</p>
          <p><span className="text-ink">Doc ID:</span> {doc.id}</p>
          {doc.provenance && (
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-mono ${PROV_BADGE[doc.provenance] ?? "bg-gray-700 text-gray-300"}`}>
              {doc.provenance}
            </span>
          )}
        </div>

        <p className="mt-3 text-xs text-ink-secondary italic border-t border-white/10 pt-3">
          {doc.explanation || result.explanation || "—"}
        </p>
      </div>
    </div>
  );
}

function EvidenceCard({ result, rank, onWhy }) {
  const doc = result;
  const sev  = (doc.severity || "").toLowerCase();
  const prov = doc.provenance || "SYNTHETIC";

  return (
    <div className="bg-surface border border-white/10 rounded-lg p-4 hover:border-accent/50 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-accent font-mono text-sm font-bold">#{rank}</span>
          <span className="font-medium text-ink">{doc.title}</span>
        </div>
        <span className="text-accent font-mono text-sm shrink-0">
          {(result.final_score ?? 0).toFixed(3)}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-2">
        {sev && (
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${SEV_BADGE[sev] ?? "bg-gray-700 text-gray-300"}`}>
            {sev.toUpperCase()}
          </span>
        )}
        <span className={`px-2 py-0.5 rounded text-xs font-mono ${PROV_BADGE[prov] ?? "bg-gray-700 text-gray-300"}`}>
          {prov}
        </span>
        {doc.hazard && (
          <span className="px-2 py-0.5 rounded text-xs bg-white/10 text-ink-secondary">
            {doc.hazard}
          </span>
        )}
      </div>

      <p className="text-sm text-ink-secondary mb-2 line-clamp-2">{doc.text}</p>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-secondary">
        <span>
          <span className="text-ink">Source:</span> {doc.source} ·{" "}
          <span className="text-ink">Date:</span> {doc.date} ·{" "}
          <span className="text-ink">ID:</span> {doc.id}
        </span>
        <button
          onClick={() => onWhy(result)}
          className="px-2 py-1 rounded border border-accent/40 text-accent text-xs hover:bg-accent/10 transition-colors"
        >
          Why ranked #{rank}?
        </button>
      </div>
    </div>
  );
}

function ParsedQueryPanel({ pq }) {
  if (!pq) return null;
  const fields = [
    ["Intent",      pq.intent],
    ["Origin",      pq.origin],
    ["Destination", pq.destination],
    ["Cargo",       pq.cargo],
    ["Hazard",      pq.hazard],
    ["Urgency",     pq.urgency],
    ["Date",        pq.date],
  ].filter(([, v]) => v);

  if (!fields.length) return null;

  return (
    <div className="bg-surface border border-white/10 rounded-lg p-4 mb-4">
      <h3 className="text-xs font-semibold text-ink-secondary uppercase tracking-wider mb-2">
        Parsed Query
      </h3>
      <div className="flex flex-wrap gap-2">
        {fields.map(([k, v]) => (
          <span key={k} className="px-2 py-1 bg-white/10 rounded text-xs">
            <span className="text-ink-secondary">{k}: </span>
            <span className="text-ink font-medium">{v}</span>
          </span>
        ))}
      </div>
      {pq.expanded_terms?.length > 0 && (
        <p className="mt-2 text-xs text-ink-secondary">
          <span className="text-ink">Expanded: </span>
          {pq.expanded_terms.slice(0, 8).join(", ")}
        </p>
      )}
    </div>
  );
}

function RoutePanel({ rec }) {
  if (!rec) return null;
  if (!rec.available) {
    return (
      <div className="bg-surface border border-white/10 rounded-lg p-4 mb-4">
        <h3 className="font-semibold text-ink mb-1">Route Planning</h3>
        <p className="text-sm text-ink-secondary">{rec.reason}</p>
      </div>
    );
  }

  const r = rec.recommended_route;
  return (
    <div className="bg-surface border border-accent/30 rounded-lg p-4 mb-4">
      <h3 className="font-semibold text-ink mb-3">
        Recommended Route — {rec.origin} → {rec.destination}
      </h3>
      {r && (
        <div className="space-y-1 text-sm text-ink-secondary">
          <p>
            <span className="text-ink">ETA:</span> {r.eta_hours?.toFixed(1)} hours ·{" "}
            <span className="text-ink">Accessibility:</span>{" "}
            <span className={r.avg_accessibility >= 60 ? "text-green-400" : "text-orange-400"}>
              {r.avg_accessibility?.toFixed(0)}
            </span>
          </p>
          {r.path?.length > 0 && (
            <p>
              <span className="text-ink">Path:</span>{" "}
              {r.path.slice(0, 5).join(" → ")}
              {r.path.length > 5 ? ` … (+${r.path.length - 5} more)` : ""}
            </p>
          )}
          {r.explanation?.reasons?.length > 0 && (
            <ul className="mt-1 list-disc list-inside">
              {r.explanation.reasons.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      {rec.alternatives?.length > 0 && (
        <details className="mt-3">
          <summary className="text-xs text-ink-secondary cursor-pointer hover:text-ink">
            {rec.alternatives.length} alternative route(s)
          </summary>
          {rec.alternatives.map((alt, i) => (
            <div key={i} className="mt-2 text-xs text-ink-secondary pl-2 border-l border-white/10">
              Alt {i + 2}: ETA {alt.eta_hours?.toFixed(1)}h ·{" "}
              Accessibility {alt.avg_accessibility?.toFixed(0)}
            </div>
          ))}
        </details>
      )}
    </div>
  );
}

// ─── main page ───────────────────────────────────────────────────────────────

export default function IntelligenceSearch() {
  const [query, setQuery]         = useState("");
  const [method, setMethod]       = useState("hybrid");
  const [cargo, setCargo]         = useState("");
  const [topK, setTopK]           = useState(10);

  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState(null);
  const [error, setError]         = useState(null);
  const [whyDoc, setWhyDoc]       = useState(null);

  const inputRef = useRef(null);

  const handleSearch = useCallback(async (e) => {
    e?.preventDefault();
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/rag/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: topK, cargo_type: cargo || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || `Error ${res.status}`);
      setResult(data);
    } catch (err) {
      setError(err.message || "Search failed");
    } finally {
      setLoading(false);
    }
  }, [query, method, cargo, topK]);

  const handleExample = (ex) => {
    setQuery(ex);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const riskColor = result ? (RISK_COLORS[result.risk_level] || RISK_COLORS.UNKNOWN) : "";

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">

      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-ink mb-2">
          LogiRush Intelligence Search
        </h1>
        <p className="text-ink-secondary max-w-xl mx-auto">
          Pan-India multi-hazard logistics retrieval — hybrid IR, semantic search,
          freshness, geographic relevance, and grounded route-risk answers.
        </p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2 mb-3">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Can I transport medicine from Guwahati to Kolkata today?"
            className="flex-1 bg-surface border border-white/20 rounded-lg px-4 py-3 text-ink placeholder-ink-secondary focus:outline-none focus:border-accent"
            aria-label="Logistics query"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-accent rounded-lg font-semibold hover:brightness-110 disabled:opacity-50 transition-all"
            style={{ color: "var(--bg-contrast)" }}
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>

        {/* Options */}
        <div className="flex flex-wrap gap-3 text-sm">
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs"
            aria-label="Retrieval method"
          >
            {METHODS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>

          <select
            value={cargo}
            onChange={(e) => setCargo(e.target.value)}
            className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs"
            aria-label="Cargo type"
          >
            {CARGO_TYPES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>

          <div className="flex items-center gap-2 text-xs text-ink-secondary">
            <label htmlFor="topk">Top-K:</label>
            <input
              id="topk"
              type="number"
              value={topK}
              onChange={(e) => setTopK(Math.max(1, Math.min(50, +e.target.value)))}
              className="w-14 bg-surface border border-white/20 rounded px-2 py-1.5 text-ink text-xs"
              min={1} max={50}
            />
          </div>
        </div>

        {/* Example queries */}
        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => handleExample(ex)}
              className="text-xs px-2 py-1 border border-white/10 rounded hover:border-accent/50 text-ink-secondary hover:text-ink transition-colors"
            >
              {ex.length > 50 ? ex.slice(0, 50) + "…" : ex}
            </button>
          ))}
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/40 rounded-lg p-4 mb-6 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div>
          {/* Risk level + answer */}
          <div className={`border rounded-lg p-5 mb-5 ${riskColor}`}>
            <div className="flex items-center gap-3 mb-3">
              <span className={`text-2xl font-bold font-mono ${riskColor.split(" ")[0]}`}>
                Route Risk: {result.risk_level ?? "UNKNOWN"}
              </span>
              <span className="text-xs text-ink-secondary">
                Latency: {result.latency_ms?.toFixed(0)} ms ·{" "}
                Method: {result.retrieval_method}
                {!result.grounded && " · LLM unavailable"}
              </span>
            </div>
            {result.note && (
              <p className="text-xs text-ink-secondary italic mb-2">{result.note}</p>
            )}
            <pre className="whitespace-pre-wrap text-sm text-ink font-sans leading-relaxed">
              {result.answer}
            </pre>
            {result.evidence_used?.length > 0 && (
              <p className="mt-2 text-xs text-ink-secondary">
                Evidence cited: {result.evidence_used.join(", ")}
              </p>
            )}
          </div>

          {/* Route recommendation */}
          {result.route_recommendation && (
            <RoutePanel rec={result.route_recommendation} />
          )}

          {/* Parsed query */}
          <ParsedQueryPanel pq={result.parsed_query} />

          {/* Evidence list */}
          {result.evidence?.length > 0 ? (
            <div>
              <h2 className="font-semibold text-ink mb-3">
                Retrieved Evidence ({result.evidence.length} documents)
              </h2>
              <div className="space-y-3">
                {result.evidence.map((r) => (
                  <EvidenceCard
                    key={r.id}
                    result={r}
                    rank={r.rank}
                    onWhy={setWhyDoc}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="text-sm text-ink-secondary bg-surface border border-white/10 rounded-lg p-4">
              Insufficient verified evidence was found for this query.
            </div>
          )}
        </div>
      )}

      {/* Why panel modal */}
      {whyDoc && <WhyPanel result={whyDoc} onClose={() => setWhyDoc(null)} />}
    </div>
  );
}
