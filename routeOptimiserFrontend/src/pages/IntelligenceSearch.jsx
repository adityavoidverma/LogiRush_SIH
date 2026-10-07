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

  return (
    <div className="bg-surface border border-white/10 rounded-lg p-4 hover:border-accent/40 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-accent font-mono text-sm font-bold shrink-0">#{rank}</span>
          <span className="font-medium text-ink">{doc.title}</span>
        </div>
        {/* Final score — labeled explicitly for IR audience */}
        <div className="text-right shrink-0">
          <span className="text-accent font-mono text-sm font-bold">{(result.final_score ?? 0).toFixed(3)}</span>
          <div className="text-[10px] text-ink-secondary">final score</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-2">
        {sev && <Badge className={SEV_BADGE[sev] ?? "bg-gray-700 text-gray-300"}>{sev.toUpperCase()}</Badge>}
        {doc.hazard && <Badge className="bg-white/10 text-ink-secondary">{doc.hazard}</Badge>}
        {doc.highway && <Badge className="bg-white/10 text-ink-secondary font-mono">{doc.highway}</Badge>}
        {doc.state && <Badge className="bg-white/10 text-ink-secondary">{doc.state}</Badge>}
        {doc.source && <Badge className="bg-white/5 text-ink-secondary/70">{doc.source}</Badge>}
      </div>

      <p className="text-sm text-ink-secondary mb-3 line-clamp-2">{doc.text}</p>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-secondary">
        <span className="font-mono">
          {doc.id} · {doc.date}
        </span>
        <button
          onClick={() => onWhy(result)}
          className="px-2 py-1 rounded border border-accent/40 text-accent text-xs hover:bg-accent/10 transition-colors"
        >
          Why ranked #{rank}? ↗
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
                <span className="text-ink font-semibold">Phrase search</span> — uses positional posting lists to find documents containing the{" "}
                <strong className="text-ink">exact consecutive token sequence</strong>.
                Time complexity O(n·k) where n = candidate docs, k = phrase length.
                Useful for exact highway names, incident phrases, or named corridors.
              </p>
              <PhraseSearchPanel />
            </>
          )}
          {tab === "proximity" && (
            <>
              <p className="text-xs text-ink-secondary mb-4">
                <span className="text-ink font-semibold">Proximity search</span> — uses positional posting lists to find documents where two terms appear{" "}
                <strong className="text-ink">within N tokens</strong> of each other.
                Captures co-occurrence of semantically related concepts without exact adjacency.
                Minimum token distance is returned per document.
              </p>
              <ProximitySearchPanel />
            </>
          )}
          {tab === "corpus"    && (
            <>
              <p className="text-xs text-ink-secondary mb-4">
                Browse all <span className="text-ink font-semibold">1,023 documents</span> currently indexed by the IR engine.
                Corpus covers 36 Indian states/UTs across 7 hazard types (flood 30%, landslide 25%, rainfall 15%, cyclone 10%, accident 10%, infrastructure 8%, heat 2%).
                Click any document to inspect its full text, metadata, and coordinates.
              </p>
              <CorpusBrowser />
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Feature pill ─────────────────────────────────────────────────────────────

function FeaturePill({ icon, label }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-white/15 bg-white/5 text-xs text-ink-secondary">
      <span>{icon}</span>
      <span>{label}</span>
    </span>
  );
}

// ─── Stats bar ────────────────────────────────────────────────────────────────

function StatsBar() {
  return (
    <div className="flex flex-wrap justify-center gap-8 mb-6">
      {[
        { value: "1,023", label: "Documents indexed" },
        { value: "4",     label: "Retrieval methods" },
        { value: "36",    label: "States / UTs" },
        { value: "7",     label: "Hazard types" },
      ].map(({ value, label }) => (
        <div key={label} className="text-center">
          <div className="text-2xl font-bold text-accent font-mono">{value}</div>
          <div className="text-xs text-ink-secondary mt-0.5">{label}</div>
        </div>
      ))}
    </div>
  );
}

// ─── Evaluation metrics banner ────────────────────────────────────────────────

function EvalBanner() {
  // Real numbers from: python3.11 -c "from src.ir.engine import ir_engine; ..."
  // Evaluated on 25-query judgement set, top_k=5
  const rows = [
    { method: "TF-IDF",  p5: "0.296", r5: "0.611", mrr: "0.800", note: "baseline" },
    { method: "BM25",    p5: "0.312", r5: "0.653", mrr: "0.805", note: "best P@5 & MRR", best: true },
    { method: "Dense",   p5: "0.248", r5: "0.516", mrr: "0.673", note: "semantic generalisation" },
    { method: "Hybrid",  p5: "0.272", r5: "0.591", mrr: "0.772", note: "multi-signal fusion" },
  ];
  return (
    <div className="border border-white/10 rounded-xl p-4 mb-6 bg-white/2">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-ink uppercase tracking-wider">
          Evaluation — 25 queries · Top-5 · Relevance judgements against 1,023-doc corpus
        </h3>
        <span className="text-[10px] text-ink-secondary border border-white/10 rounded px-2 py-0.5 font-mono">
          P@5 · R@5 · MRR
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-ink-secondary border-b border-white/10">
              <th className="text-left pb-2 font-medium">Method</th>
              <th className="text-right pb-2 font-medium">P@5</th>
              <th className="text-right pb-2 font-medium">R@5</th>
              <th className="text-right pb-2 font-medium">MRR</th>
              <th className="text-left pb-2 font-medium pl-4 hidden sm:table-cell">Note</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.method}
                className={`border-b border-white/5 ${r.best ? "text-accent" : "text-ink-secondary"}`}>
                <td className="py-1.5 font-mono font-medium">{r.method}</td>
                <td className={`py-1.5 text-right font-mono ${r.best ? "font-bold" : ""}`}>{r.p5}</td>
                <td className={`py-1.5 text-right font-mono ${r.best ? "font-bold" : ""}`}>{r.r5}</td>
                <td className={`py-1.5 text-right font-mono ${r.best ? "font-bold" : ""}`}>{r.mrr}</td>
                <td className="py-1.5 pl-4 hidden sm:table-cell text-ink-secondary/60">{r.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[10px] text-ink-secondary mt-2">
        BM25 leads on precision-focused queries where exact highway/location terms dominate.
        Hybrid fusion benefits queries with broader semantic intent.
        Dense lower here due to exact-match bias in judgement set.
      </p>
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

      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <div className="mb-8 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/30 text-accent text-xs font-medium mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse inline-block" />
          Live IR System · RAG-augmented
        </div>
        <h1 className="text-3xl font-bold text-ink mb-2 tracking-tight">
          LogiRush Intelligence Search
        </h1>
        <p className="text-ink-secondary max-w-2xl mx-auto text-sm mb-5">
          A multi-method information retrieval engine over a 1,023-document logistics hazard corpus.
          Supports BM25, TF-IDF, dense vector retrieval (all-MiniLM-L6-v2), and hybrid score fusion —
          with query expansion, freshness decay, authority scoring, and RAG-grounded answers.
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2 mb-6">
          <FeaturePill icon="📖" label="Inverted Index + Positional Postings" />
          <FeaturePill icon="⚖️" label="BM25  k₁=1.5  b=0.75" />
          <FeaturePill icon="🧠" label="Dense: all-MiniLM-L6-v2 (384-dim)" />
          <FeaturePill icon="🔀" label="Hybrid Fusion  0.45·BM25 + 0.35·Semantic + 0.10·Freshness + 0.10·Authority" />
          <FeaturePill icon="🔍" label="Phrase & Proximity Search" />
          <FeaturePill icon="💬" label="RAG  (Groq LLM)" />
        </div>

        {/* Corpus stats */}
        <StatsBar />
      </div>

      {/* ── Evaluation metrics banner ─────────────────────────────────── */}
      <EvalBanner />

      {/* ── IR Architecture note ──────────────────────────────────────── */}
      <div className="bg-white/3 border border-white/10 rounded-xl px-5 py-4 mb-6 text-xs text-ink-secondary leading-relaxed">
        <span className="text-ink font-semibold text-sm">Pipeline: </span>
        Raw query
        <span className="mx-1 text-accent">→</span> Query parser + expansion (HAZARD_SYNONYMS)
        <span className="mx-1 text-accent">→</span> BM25 (Okapi) + TF-IDF + Dense cosine similarity (3×top-K candidates)
        <span className="mx-1 text-accent">→</span> Score fusion + geographic boost
        <span className="mx-1 text-accent">→</span> Top-K re-ranked results
        <span className="mx-1 text-accent">→</span> RAG grounding (Groq / OpenAI / structured fallback)
      </div>

      {/* ── Main search ───────────────────────────────────────────────── */}
      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2 mb-3">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="e.g. Can I transport medicine from Guwahati to Kolkata today?"
            className="flex-1 bg-surface border border-white/20 rounded-lg px-4 py-3 text-ink placeholder-ink-secondary focus:outline-none focus:border-accent text-sm"
            aria-label="Logistics query"
          />
          <button type="submit" disabled={loading || !query.trim()}
            className="px-6 py-3 bg-accent rounded-lg font-semibold hover:brightness-110 disabled:opacity-50 transition-all text-sm"
            style={{ color: "var(--bg-contrast)" }}>
            {loading ? "Searching…" : "Search"}
          </button>
        </div>

        {/* Controls row — labeled for IR audience */}
        <div className="flex flex-wrap gap-3 mb-3 items-center">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] text-ink-secondary uppercase tracking-wider pl-1">Retrieval Method</span>
            <select value={method} onChange={e => setMethod(e.target.value)}
              className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs"
              aria-label="Retrieval method">
              {METHODS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] text-ink-secondary uppercase tracking-wider pl-1">Cargo Type</span>
            <select value={cargo} onChange={e => setCargo(e.target.value)}
              className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs"
              aria-label="Cargo type">
              {CARGO_TYPES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] text-ink-secondary uppercase tracking-wider pl-1">Top-K</span>
            <input id="topk" type="number" value={topK}
              onChange={e => setTopK(Math.max(1, Math.min(50, +e.target.value)))}
              className="w-16 bg-surface border border-white/20 rounded px-2 py-1.5 text-ink text-xs text-center"
              min={1} max={50} />
          </div>
        </div>

        {/* Example queries */}
        <div className="flex flex-wrap gap-1.5">
          <span className="text-[10px] text-ink-secondary self-center mr-1 uppercase tracking-wider">Try:</span>
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

      {/* ── Error ─────────────────────────────────────────────────────── */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/40 rounded-lg p-4 mb-6 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* ── Results ───────────────────────────────────────────────────── */}
      {result && (
        <div>

          {/* ── Retrieval run metadata bar ── */}
          <div className="flex flex-wrap gap-x-5 gap-y-1.5 px-4 py-3 mb-4 bg-white/3 border border-white/10 rounded-lg text-xs text-ink-secondary">
            <span><span className="text-ink font-medium">Method:</span> {result.retrieval_method}</span>
            <span><span className="text-ink font-medium">Latency:</span> {result.latency_ms?.toFixed(0)} ms</span>
            <span><span className="text-ink font-medium">Docs retrieved:</span> {result.evidence?.length ?? 0} / top-{topK}</span>
            <span><span className="text-ink font-medium">Corpus size:</span> 1,023 docs</span>
            <span><span className="text-ink font-medium">LLM:</span> {result.grounded ? result.provider : "structured fallback (no LLM)"}</span>
            {result.grounded && (
              <span className="text-green-400">✓ RAG-grounded answer</span>
            )}
          </div>

          {/* ── Parsed query ── */}
          <ParsedQueryPanel pq={result.parsed_query} />

          {/* ── RAG answer / risk panel ── */}
          <div className={`border-2 rounded-xl p-5 mb-5 ${riskColor}`}>
            <div className="flex flex-wrap items-center gap-3 mb-3">
              <span className={`text-2xl font-bold font-mono tracking-tight ${riskColor.split(" ")[0]}`}>
                Route Risk: {result.risk_level ?? "UNKNOWN"}
              </span>
              {result.grounded && result.provider && (
                <span className="text-xs text-green-400 border border-green-400/30 rounded px-2 py-0.5">
                  ✓ Grounded by {result.provider}
                </span>
              )}
              {!result.grounded && (
                <span className="text-xs text-yellow-400/80 border border-yellow-400/20 rounded px-2 py-0.5">
                  ⚠ Structured fallback — no LLM
                </span>
              )}
            </div>

            {result.note && (
              <p className="text-xs text-yellow-400/80 italic mb-3">⚠ {result.note}</p>
            )}

            <div className="text-sm text-ink leading-relaxed whitespace-pre-wrap"
                 dangerouslySetInnerHTML={{ __html:
                   (result.answer || "").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
                 }} />

            {result.evidence_used?.length > 0 && (
              <p className="mt-4 text-xs text-ink-secondary border-t border-white/10 pt-3 font-mono">
                Evidence cited: {result.evidence_used.join(" · ")}
              </p>
            )}
          </div>

          {/* ── Route recommendation ── */}
          {result.route_recommendation && <RoutePanel rec={result.route_recommendation} />}

          {/* ── Retrieved evidence ── */}
          {result.evidence?.length > 0 ? (
            <div>
              {/* Section header with IR terminology */}
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
                  Retrieved Evidence
                  <span className="ml-2 text-ink font-mono normal-case">
                    ({result.evidence.length} doc{result.evidence.length !== 1 ? "s" : ""}, ranked by {result.retrieval_method} score)
                  </span>
                </h2>
                <span className="text-[10px] text-ink-secondary border border-white/10 rounded px-2 py-0.5">
                  Click "Why ranked #N?" to inspect per-signal score breakdown
                </span>
              </div>

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

      {/* ── Why-ranked modal ──────────────────────────────────────────── */}
      {whyDoc && <WhyPanel result={whyDoc} onClose={() => setWhyDoc(null)} method={result?.retrieval_method || "hybrid"} />}
    </div>
  );
}
