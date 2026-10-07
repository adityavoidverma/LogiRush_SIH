// src/pages/IntelligenceSearch.jsx
// LogiRush: Pan-India Multi-Hazard Logistics Intelligence Search

import { useState, useCallback, useRef } from "react";
import { API_BASE_URL } from "../api/client";

// ─── constants ───────────────────────────────────────────────────────────────

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
  CRITICAL:            "text-red-500 border-red-500",
  HIGH:                "text-orange-400 border-orange-400",
  MEDIUM:              "text-yellow-400 border-yellow-400",
  LOW:                 "text-green-400 border-green-400",
  "INSUFFICIENT DATA": "text-gray-400 border-gray-500",
  UNKNOWN:             "text-gray-400 border-gray-400",
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

// ─── reusable atoms ───────────────────────────────────────────────────────────

function ScoreBar({ label, value }) {
  const pct = Math.round(Math.min(value, 1) * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-ink-secondary text-right shrink-0">{label}</span>
      <div className="flex-1 bg-white/10 rounded-full h-1.5">
        <div className="h-1.5 rounded-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-ink font-mono">{value.toFixed(3)}</span>
    </div>
  );
}

function Badge({ children, className = "" }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${className}`}>
      {children}
    </span>
  );
}

function SectionHeading({ children }) {
  return (
    <h2 className="text-xs font-semibold text-ink-secondary uppercase tracking-wider mb-3">
      {children}
    </h2>
  );
}

// ─── Why-ranked modal ─────────────────────────────────────────────────────────

// Which score fields actually DROVE the final score for each method
const METHOD_ACTIVE_SCORES = {
  hybrid:  ["bm25", "tfidf", "semantic", "freshness", "geographic", "authority"],
  bm25:    ["bm25"],
  tfidf:   ["tfidf"],
  dense:   ["semantic"],
};

// Which are shown as informational (visible but greyed, did NOT affect final score)
const METHOD_INFO_SCORES = {
  hybrid:  [],
  bm25:    ["freshness", "geographic", "authority"],
  tfidf:   ["freshness", "geographic", "authority"],
  dense:   ["freshness", "geographic", "authority"],
};

const SCORE_LABELS = {
  bm25:      "BM25 relevance",
  tfidf:     "TF-IDF relevance",
  semantic:  "Semantic similarity",
  freshness: "Freshness",
  geographic:"Geographic",
  authority: "Source authority",
};

function WhyPanel({ result, onClose, method = "hybrid" }) {
  const doc    = result;
  const scores = result.scores || {};
  const active = METHOD_ACTIVE_SCORES[method] || METHOD_ACTIVE_SCORES.hybrid;
  const info   = (METHOD_INFO_SCORES[method]  || []);

  const methodLabel = {
    hybrid: "Hybrid (BM25 + Semantic + Freshness + Authority)",
    bm25:   "BM25 only",
    tfidf:  "TF-IDF only",
    dense:  "Dense / Semantic only",
  }[method] || method;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-surface border border-white/20 rounded-xl p-6 max-w-lg w-full shadow-2xl">
        <div className="flex justify-between items-start mb-1">
          <h3 className="font-semibold text-ink">Why ranked #{result.rank}?</h3>
          <button onClick={onClose} className="text-ink-secondary hover:text-ink text-xl leading-none">✕</button>
        </div>
        <p className="text-xs text-ink-secondary mb-4">
          Method: <span className="text-accent">{methodLabel}</span>
        </p>

        <div className="space-y-2 mb-2">
          {Object.entries(SCORE_LABELS).map(([key, label]) => {
            const value  = scores[key] ?? 0;
            const isActive = active.includes(key);
            const isInfo   = info.includes(key);
            // inactive = not active and not info
            const isInactive = !isActive && !isInfo;

            return (
              <div key={key} className={`flex items-center gap-2 text-xs ${isInactive ? "opacity-20" : isInfo ? "opacity-50" : ""}`}>
                <span className="w-28 text-ink-secondary text-right shrink-0">{label}</span>
                <div className="flex-1 bg-white/10 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${isActive ? "bg-accent" : isInfo ? "bg-white/40" : "bg-white/20"}`}
                    style={{ width: `${Math.round(Math.min(value, 1) * 100)}%` }}
                  />
                </div>
                <span className={`w-10 text-right font-mono ${isActive ? "text-ink" : "text-ink-secondary"}`}>
                  {isInactive ? "—" : value.toFixed(3)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex gap-4 text-xs text-ink-secondary mb-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-accent inline-block" />
            drove final score
          </span>
          {info.length > 0 && (
            <span className="flex items-center gap-1.5 opacity-50">
              <span className="w-2 h-2 rounded-full bg-white/40 inline-block" />
              info only (not used)
            </span>
          )}
        </div>

        <div className="border-t border-white/10 pt-3 mb-4">
          <ScoreBar label="Final score" value={result.final_score ?? 0} />
          {method !== "hybrid" && (
            <p className="text-xs text-ink-secondary mt-1 pl-1">
              = {SCORE_LABELS[active[0]]} score only
            </p>
          )}
        </div>

        <div className="text-xs text-ink-secondary space-y-1">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <p><span className="text-ink">Source:</span> {doc.source}</p>
            <p><span className="text-ink">Type:</span> {doc.source_type}</p>
            <p><span className="text-ink">Date:</span> {doc.date}</p>
            <p><span className="text-ink">Hazard:</span> {doc.hazard}</p>
            <p><span className="text-ink">Severity:</span> {doc.severity}</p>
            <p><span className="text-ink">Doc ID:</span> <span className="font-mono">{doc.id}</span></p>
          </div>
          <p className="pt-1"><span className="text-ink">Location:</span> {doc.location}</p>
          {doc.provenance && (
            <Badge className={PROV_BADGE[doc.provenance] ?? "bg-gray-700 text-gray-300"}>
              {doc.provenance}
            </Badge>
          )}
        </div>

        {(doc.explanation || result.explanation) && (
          <p className="mt-3 text-xs text-ink-secondary italic border-t border-white/10 pt-3">
            {doc.explanation || result.explanation}
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Evidence card ────────────────────────────────────────────────────────────

function EvidenceCard({ result, rank, onWhy }) {
  const doc = result;
  const sev  = (doc.severity || "").toLowerCase();
  const prov = doc.provenance || "SYNTHETIC";

  return (
    <div className="bg-surface border border-white/10 rounded-lg p-4 hover:border-accent/40 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-accent font-mono text-sm font-bold shrink-0">#{rank}</span>
          <span className="font-medium text-ink">{doc.title}</span>
        </div>
        <span className="text-accent font-mono text-sm shrink-0">
          {(result.final_score ?? 0).toFixed(3)}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-2">
        {sev && <Badge className={SEV_BADGE[sev] ?? "bg-gray-700 text-gray-300"}>{sev.toUpperCase()}</Badge>}
        <Badge className={PROV_BADGE[prov] ?? "bg-gray-700 text-gray-300"}>{prov}</Badge>
        {doc.hazard && <Badge className="bg-white/10 text-ink-secondary">{doc.hazard}</Badge>}
        {doc.highway && <Badge className="bg-white/10 text-ink-secondary font-mono">{doc.highway}</Badge>}
        {doc.state && <Badge className="bg-white/10 text-ink-secondary">{doc.state}</Badge>}
      </div>

      <p className="text-sm text-ink-secondary mb-3 line-clamp-2">{doc.text}</p>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-secondary">
        <span>
          <span className="text-ink">Source:</span> {doc.source} ·{" "}
          <span className="text-ink">Date:</span> {doc.date} ·{" "}
          <span className="text-ink font-mono">{doc.id}</span>
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

// ─── Parsed query pill row ────────────────────────────────────────────────────

function ParsedQueryPanel({ pq }) {
  if (!pq) return null;
  const fields = [
    ["Intent", pq.intent], ["Origin", pq.origin], ["Destination", pq.destination],
    ["Cargo", pq.cargo], ["Hazard", pq.hazard], ["Urgency", pq.urgency], ["Date", pq.date],
  ].filter(([, v]) => v);
  if (!fields.length) return null;

  return (
    <div className="bg-surface border border-white/10 rounded-lg p-4 mb-4">
      <SectionHeading>Parsed Query</SectionHeading>
      <div className="flex flex-wrap gap-2 mb-2">
        {fields.map(([k, v]) => (
          <span key={k} className="px-2 py-1 bg-white/10 rounded text-xs">
            <span className="text-ink-secondary">{k}: </span>
            <span className="text-ink font-medium">{v}</span>
          </span>
        ))}
      </div>
      {pq.expanded_terms?.length > 0 && (
        <p className="text-xs text-ink-secondary">
          <span className="text-ink">Expanded terms: </span>
          {pq.expanded_terms.slice(0, 10).join(", ")}
        </p>
      )}
    </div>
  );
}

// ─── Route recommendation panel ───────────────────────────────────────────────

function RoutePanel({ rec }) {
  if (!rec) return null;
  if (!rec.available) {
    return (
      <div className="bg-surface border border-white/10 rounded-lg p-4 mb-4">
        <SectionHeading>Route Planning</SectionHeading>
        <p className="text-sm text-ink-secondary">{rec.reason}</p>
      </div>
    );
  }
  const r = rec.recommended_route;
  return (
    <div className="bg-surface border border-accent/30 rounded-lg p-4 mb-4">
      <SectionHeading>Recommended Route — {rec.origin} → {rec.destination}</SectionHeading>
      {r && (
        <div className="space-y-1 text-sm text-ink-secondary">
          <p>
            <span className="text-ink">ETA:</span> {r.eta_hours?.toFixed(1)}h ·{" "}
            <span className="text-ink">Accessibility:</span>{" "}
            <span className={r.avg_accessibility >= 60 ? "text-green-400" : "text-orange-400"}>
              {r.avg_accessibility?.toFixed(0)}
            </span>
          </p>
          {r.path?.length > 0 && (
            <p><span className="text-ink">Path:</span> {r.path.slice(0, 5).join(" → ")}
              {r.path.length > 5 ? ` … (+${r.path.length - 5})` : ""}</p>
          )}
          {r.explanation?.reasons?.length > 0 && (
            <ul className="mt-1 list-disc list-inside">
              {r.explanation.reasons.map((reason, i) => <li key={i}>{reason}</li>)}
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
              Alt {i + 2}: ETA {alt.eta_hours?.toFixed(1)}h · Accessibility {alt.avg_accessibility?.toFixed(0)}
            </div>
          ))}
        </details>
      )}
    </div>
  );
}

// ─── Phrase Search panel ──────────────────────────────────────────────────────

function PhraseSearchPanel() {
  const [phrase, setPhrase]   = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const run = async (e) => {
    e.preventDefault();
    if (!phrase.trim()) return;
    setLoading(true); setError(null); setResults(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/ir/phrase?q=${encodeURIComponent(phrase)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || `Error ${res.status}`);
      setResults(data);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const EXAMPLES = ["NH27 flooding", "Brahmaputra overflow", "landslide blocked", "red alert rainfall"];

  return (
    <div>
      <form onSubmit={run} className="flex gap-2 mb-3">
        <input
          value={phrase}
          onChange={e => setPhrase(e.target.value)}
          placeholder='e.g. "NH27 flooding" or "landslide blocked"'
          className="flex-1 bg-surface border border-white/20 rounded-lg px-3 py-2 text-sm text-ink placeholder-ink-secondary focus:outline-none focus:border-accent"
          aria-label="Phrase to search"
        />
        <button
          type="submit"
          disabled={loading || !phrase.trim()}
          className="px-4 py-2 bg-accent rounded-lg text-sm font-semibold hover:brightness-110 disabled:opacity-50 transition-all"
          style={{ color: "var(--bg-contrast)" }}
        >
          {loading ? "…" : "Search"}
        </button>
      </form>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {EXAMPLES.map(ex => (
          <button key={ex} type="button" onClick={() => setPhrase(ex)}
            className="text-xs px-2 py-0.5 border border-white/10 rounded text-ink-secondary hover:text-ink hover:border-accent/40 transition-colors">
            {ex}
          </button>
        ))}
      </div>

      {error && <p className="text-red-400 text-xs mb-2">{error}</p>}

      {results && (
        <div>
          <p className="text-xs text-ink-secondary mb-2">
            Found <span className="text-ink font-medium">{results.count}</span> document(s) containing
            <span className="text-accent font-mono"> "{results.phrase}"</span>
          </p>
          {results.count === 0 && (
            <p className="text-sm text-ink-secondary bg-surface border border-white/10 rounded p-3">
              No documents in the corpus contain this exact phrase.
            </p>
          )}
          <div className="space-y-2">
            {results.results.map(r => (
              <div key={r.doc_id} className="bg-surface border border-white/10 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm text-ink">{r.title}</span>
                  <div className="flex items-center gap-2">
                    <Badge className={PROV_BADGE[r.provenance] ?? "bg-gray-700 text-gray-300"}>{r.provenance}</Badge>
                    <span className="text-xs text-accent font-mono">{r.match_count}× match</span>
                  </div>
                </div>
                {/* Snippet with highlighted tokens */}
                <p className="text-xs text-ink-secondary font-mono leading-relaxed"
                   dangerouslySetInnerHTML={{ __html:
                     (r.snippet || "").replace(/\*\*([^*]+)\*\*/g,
                       '<mark class="bg-accent/20 text-accent not-italic px-0.5 rounded">$1</mark>')
                   }} />
                <p className="text-xs text-ink-secondary mt-1">
                  <span className="font-mono text-ink">{r.doc_id}</span> · {r.source} · {r.date}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Proximity Search panel ───────────────────────────────────────────────────

function ProximitySearchPanel() {
  const [t1, setT1]           = useState("");
  const [t2, setT2]           = useState("");
  const [window_, setWindow]  = useState(10);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const run = async (e) => {
    e.preventDefault();
    if (!t1.trim() || !t2.trim()) return;
    setLoading(true); setError(null); setResults(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/ir/proximity?t1=${encodeURIComponent(t1)}&t2=${encodeURIComponent(t2)}&window=${window_}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || `Error ${res.status}`);
      setResults(data);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const EXAMPLES = [
    ["flood", "Guwahati"], ["landslide", "Sikkim"], ["cyclone", "Odisha"], ["rainfall", "blocked"],
  ];

  return (
    <div>
      <form onSubmit={run} className="space-y-3 mb-3">
        <div className="flex gap-2 items-center">
          <input value={t1} onChange={e => setT1(e.target.value)} placeholder="Term 1  e.g. flood"
            className="flex-1 bg-surface border border-white/20 rounded-lg px-3 py-2 text-sm text-ink placeholder-ink-secondary focus:outline-none focus:border-accent"
            aria-label="First term" />
          <span className="text-ink-secondary text-sm shrink-0">within</span>
          <input type="number" value={window_} onChange={e => setWindow(Math.max(1, Math.min(50, +e.target.value)))}
            className="w-14 bg-surface border border-white/20 rounded px-2 py-2 text-ink text-sm text-center"
            min={1} max={50} aria-label="Token window" />
          <span className="text-ink-secondary text-sm shrink-0">tokens of</span>
          <input value={t2} onChange={e => setT2(e.target.value)} placeholder="Term 2  e.g. Guwahati"
            className="flex-1 bg-surface border border-white/20 rounded-lg px-3 py-2 text-sm text-ink placeholder-ink-secondary focus:outline-none focus:border-accent"
            aria-label="Second term" />
          <button type="submit" disabled={loading || !t1.trim() || !t2.trim()}
            className="px-4 py-2 bg-accent rounded-lg text-sm font-semibold hover:brightness-110 disabled:opacity-50 transition-all shrink-0"
            style={{ color: "var(--bg-contrast)" }}>
            {loading ? "…" : "Search"}
          </button>
        </div>
      </form>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {EXAMPLES.map(([a, b]) => (
          <button key={a + b} type="button" onClick={() => { setT1(a); setT2(b); }}
            className="text-xs px-2 py-0.5 border border-white/10 rounded text-ink-secondary hover:text-ink hover:border-accent/40 transition-colors">
            {a} ↔ {b}
          </button>
        ))}
      </div>

      {error && <p className="text-red-400 text-xs mb-2">{error}</p>}

      {results && (
        <div>
          <p className="text-xs text-ink-secondary mb-2">
            Found <span className="text-ink font-medium">{results.count}</span> document(s) where
            <span className="text-accent font-mono"> "{results.term1}"</span> and
            <span className="text-accent font-mono"> "{results.term2}"</span> appear within {results.window} tokens
          </p>
          {results.count === 0 && (
            <p className="text-sm text-ink-secondary bg-surface border border-white/10 rounded p-3">
              No documents found. Try increasing the window size.
            </p>
          )}
          <div className="space-y-2">
            {results.results.map(r => (
              <div key={r.doc_id} className="bg-surface border border-white/10 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm text-ink">{r.title}</span>
                  <span className="text-xs text-accent font-mono">dist: {r.min_distance} tokens</span>
                </div>
                <p className="text-xs text-ink-secondary font-mono leading-relaxed"
                   dangerouslySetInnerHTML={{ __html:
                     (r.snippet || "").replace(/\*\*([^*]+)\*\*/g,
                       '<mark class="bg-accent/20 text-accent not-italic px-0.5 rounded">$1</mark>')
                   }} />
                <p className="text-xs text-ink-secondary mt-1">
                  <span className="font-mono text-ink">{r.doc_id}</span> · {r.source} · {r.date}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Corpus browser ───────────────────────────────────────────────────────────

function CorpusBrowser() {
  const [docs, setDocs]         = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [hazardF, setHazardF]   = useState("");
  const [stateF, setStateF]     = useState("");
  const [expanded, setExpanded] = useState(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams();
      if (hazardF) params.set("hazard", hazardF);
      if (stateF)  params.set("state", stateF);
      const res  = await fetch(`${API_BASE_URL}/api/ir/corpus?${params}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || `Error ${res.status}`);
      setDocs(data);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const HAZARDS = ["", "flood", "landslide", "cyclone", "rainfall", "heat", "accident", "infra", "road_block"];

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-3">
        <select value={hazardF} onChange={e => setHazardF(e.target.value)}
          className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs">
          {HAZARDS.map(h => <option key={h} value={h}>{h || "All hazards"}</option>)}
        </select>
        <input value={stateF} onChange={e => setStateF(e.target.value)}
          placeholder="State filter…"
          className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs w-36 focus:outline-none focus:border-accent"
          aria-label="Filter by state" />
        <button onClick={load} disabled={loading}
          className="px-4 py-1.5 bg-accent rounded text-xs font-semibold hover:brightness-110 disabled:opacity-50 transition-all"
          style={{ color: "var(--bg-contrast)" }}>
          {loading ? "Loading…" : "Browse Corpus"}
        </button>
      </div>

      {error && <p className="text-red-400 text-xs mb-2">{error}</p>}

      {docs && (
        <div>
          <p className="text-xs text-ink-secondary mb-3">
            Showing <span className="text-ink font-medium">{docs.total}</span> document(s) in the index
          </p>
          <div className="space-y-1.5">
            {docs.documents.map(doc => (
              <div key={doc.id} className="bg-surface border border-white/10 rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpanded(expanded === doc.id ? null : doc.id)}
                  className="w-full text-left px-4 py-2.5 flex items-center justify-between hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs text-ink-secondary">{doc.id}</span>
                    <span className="text-sm text-ink">{doc.title}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge className={SEV_BADGE[(doc.severity||"").toLowerCase()] ?? "bg-gray-700 text-gray-300"}>
                      {doc.severity}
                    </Badge>
                    <span className="text-ink-secondary text-xs">{expanded === doc.id ? "▲" : "▼"}</span>
                  </div>
                </button>

                {expanded === doc.id && (
                  <div className="px-4 pb-3 border-t border-white/10 pt-3 text-xs text-ink-secondary space-y-1.5">
                    <p className="text-ink text-sm leading-relaxed">{doc.text}</p>
                    <div className="grid grid-cols-2 gap-x-6 gap-y-1 pt-2">
                      <p><span className="text-ink">Source:</span> {doc.source} ({doc.source_type})</p>
                      <p><span className="text-ink">Date:</span> {doc.date}</p>
                      <p><span className="text-ink">Location:</span> {doc.location}</p>
                      <p><span className="text-ink">Hazard:</span> {doc.hazard}</p>
                      {doc.state    && <p><span className="text-ink">State:</span> {doc.state}</p>}
                      {doc.highway  && <p><span className="text-ink">Highway:</span> <span className="font-mono">{doc.highway}</span></p>}
                      {doc.latitude && <p><span className="text-ink">Coords:</span> {doc.latitude.toFixed(4)}, {doc.longitude.toFixed(4)}</p>}
                      {doc.provenance && (
                        <p>
                          <span className="text-ink">Provenance:</span>{" "}
                          <Badge className={PROV_BADGE[doc.provenance] ?? "bg-gray-700 text-gray-300"}>
                            {doc.provenance}
                          </Badge>
                        </p>
                      )}
                    </div>
                    {doc.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {doc.tags.map(t => (
                          <span key={t} className="px-1.5 py-0.5 bg-white/10 rounded text-ink-secondary">{t}</span>
                        ))}
                      </div>
                    )}
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

// ─── Advanced Search tabs (Phrase / Proximity / Corpus) ───────────────────────

const ADV_TABS = [
  { id: "phrase",    label: "Phrase Search" },
  { id: "proximity", label: "Proximity Search" },
  { id: "corpus",    label: "Corpus Browser" },
];

function AdvancedSearchSection() {
  const [tab, setTab] = useState(null); // null = collapsed

  return (
    <div className="border border-white/10 rounded-xl overflow-hidden mb-6">
      {/* Tab bar — clicking the active tab collapses the section */}
      <div className="flex border-b border-white/10 bg-surface/50">
        {ADV_TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(prev => prev === t.id ? null : t.id)}
            className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === t.id
                ? "bg-accent/10 text-accent border-b-2 border-accent"
                : "text-ink-secondary hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab && (
        <div className="p-5">
          {tab === "phrase"    && (
            <>
              <p className="text-xs text-ink-secondary mb-4">
                Finds documents containing the <strong className="text-ink">exact consecutive token sequence</strong>.
                Useful for specific highway names, exact incident phrases, or named corridors.
              </p>
              <PhraseSearchPanel />
            </>
          )}
          {tab === "proximity" && (
            <>
              <p className="text-xs text-ink-secondary mb-4">
                Finds documents where two terms appear <strong className="text-ink">within N tokens</strong> of each other —
                captures related co-occurring concepts even when not adjacent.
              </p>
              <ProximitySearchPanel />
            </>
          )}
          {tab === "corpus"    && (
            <>
              <p className="text-xs text-ink-secondary mb-4">
                Browse all documents indexed by the IR engine. Click any document to see its full text,
                metadata, provenance label, and coordinates. Use filters to narrow by hazard, state, or data type.
              </p>
              <CorpusBrowser />
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function IntelligenceSearch() {
  const [query, setQuery]     = useState("");
  const [method, setMethod]   = useState("hybrid");
  const [cargo, setCargo]     = useState("");
  const [topK, setTopK]       = useState(10);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState(null);
  const [whyDoc, setWhyDoc]   = useState(null);
  const inputRef = useRef(null);

  const handleSearch = useCallback(async (e) => {
    e?.preventDefault();
    const q = query.trim();
    if (!q) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/rag/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: topK, cargo_type: cargo || undefined, method }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || `Error ${res.status}`);
      setResult(data);
    } catch (err) { setError(err.message || "Search failed"); }
    finally { setLoading(false); }
  }, [query, cargo, topK]);

  const handleExample = (ex) => {
    setQuery(ex);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const riskKey   = result?.risk_level?.replace(" ", "_") ?? "UNKNOWN";
  const riskColor = RISK_COLORS[result?.risk_level] || RISK_COLORS.UNKNOWN;

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">

      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-ink mb-2">LogiRush Intelligence Search</h1>
        <p className="text-ink-secondary max-w-xl mx-auto text-sm">
          Pan-India multi-hazard · Hybrid IR · Grounded answers · Phrase & proximity search
        </p>
      </div>

      {/* Main search */}
      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2 mb-3">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="e.g. Can I transport medicine from Guwahati to Kolkata today?"
            className="flex-1 bg-surface border border-white/20 rounded-lg px-4 py-3 text-ink placeholder-ink-secondary focus:outline-none focus:border-accent"
            aria-label="Logistics query"
          />
          <button type="submit" disabled={loading || !query.trim()}
            className="px-6 py-3 bg-accent rounded-lg font-semibold hover:brightness-110 disabled:opacity-50 transition-all"
            style={{ color: "var(--bg-contrast)" }}>
            {loading ? "Searching…" : "Search"}
          </button>
        </div>

        <div className="flex flex-wrap gap-3 mb-3">
          <select value={method} onChange={e => setMethod(e.target.value)}
            className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs"
            aria-label="Retrieval method">
            {METHODS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
          <select value={cargo} onChange={e => setCargo(e.target.value)}
            className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs"
            aria-label="Cargo type">
            {CARGO_TYPES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <div className="flex items-center gap-2 text-xs text-ink-secondary">
            <label htmlFor="topk">Top-K:</label>
            <input id="topk" type="number" value={topK}
              onChange={e => setTopK(Math.max(1, Math.min(50, +e.target.value)))}
              className="w-14 bg-surface border border-white/20 rounded px-2 py-1.5 text-ink text-xs"
              min={1} max={50} />
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {EXAMPLE_QUERIES.map(ex => (
            <button key={ex} type="button" onClick={() => handleExample(ex)}
              className="text-xs px-2 py-1 border border-white/10 rounded hover:border-accent/50 text-ink-secondary hover:text-ink transition-colors">
              {ex.length > 48 ? ex.slice(0, 48) + "…" : ex}
            </button>
          ))}
        </div>
      </form>

      {/* Advanced search: phrase / proximity / corpus */}
      <AdvancedSearchSection />

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/40 rounded-lg p-4 mb-6 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div>
          {/* Risk + answer */}
          <div className={`border rounded-xl p-5 mb-5 ${riskColor}`}>
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className={`text-2xl font-bold font-mono ${riskColor.split(" ")[0]}`}>
                Route Risk: {result.risk_level ?? "UNKNOWN"}
              </span>
              <span className="text-xs text-ink-secondary">
                {result.latency_ms?.toFixed(0)} ms · {result.retrieval_method} · LLM: {result.grounded ? result.provider : "fallback"}
              </span>
            </div>

            {result.grounded && result.provider && (
              <p className="text-xs text-green-400/80 mb-2">✓ Grounded by {result.provider}</p>
            )}
            {result.note && (
              <p className="text-xs text-yellow-400/80 italic mb-2">⚠ {result.note}</p>
            )}

            {/* Render markdown-style bold */}
            <div className="text-sm text-ink leading-relaxed whitespace-pre-wrap"
                 dangerouslySetInnerHTML={{ __html:
                   (result.answer || "").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
                 }} />

            {result.evidence_used?.length > 0 && (
              <p className="mt-3 text-xs text-ink-secondary border-t border-white/10 pt-2">
                Evidence cited: {result.evidence_used.join(", ")}
              </p>
            )}
          </div>

          {/* Route recommendation */}
          {result.route_recommendation && <RoutePanel rec={result.route_recommendation} />}

          {/* Parsed query */}
          <ParsedQueryPanel pq={result.parsed_query} />

          {/* Evidence */}
          {result.evidence?.length > 0 ? (
            <div>
              <SectionHeading>
                Retrieved Evidence — {result.evidence.length} document{result.evidence.length !== 1 ? "s" : ""}
              </SectionHeading>
              <div className="space-y-3">
                {result.evidence.map(r => (
                  <EvidenceCard key={r.id} result={r} rank={r.rank} onWhy={setWhyDoc} />
                ))}
              </div>
            </div>
          ) : (
            <div className="text-sm text-ink-secondary bg-surface border border-white/10 rounded-lg p-4">
              No evidence found for this query in the current corpus.
            </div>
          )}
        </div>
      )}

      {/* Why modal */}
      {whyDoc && <WhyPanel result={whyDoc} onClose={() => setWhyDoc(null)} method={result?.retrieval_method || "hybrid"} />}
    </div>
  );
}
