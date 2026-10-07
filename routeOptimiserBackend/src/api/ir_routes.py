# src/api/ir_routes.py
"""
IR + RAG API endpoints.

POST /api/search           — hybrid / bm25 / tfidf / dense retrieval
POST /api/rag/query        — retrieval + grounded answer + route recommendation
GET  /api/search/<doc_id>  — single document + score explanation
GET  /api/ir/boolean       — Boolean retrieval (AND / OR / NOT)
GET  /api/evaluation/results — run evaluation and return metrics table
GET  /api/ir/status        — index health
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from src.ir.engine import ir_engine
from src.ir.rag import generate_answer
from src.ir.query.parser import parse_query
from src.ir.query.expansion import expand_query

logger = logging.getLogger("api.ir")

ir_bp = Blueprint("ir", __name__, url_prefix="/api")


def _err(msg: str, status: int = 400):
    return jsonify({"status": "error", "message": msg}), status


# ─────────────────────────────────────────────────────────────────
# POST /api/search
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/search", methods=["POST"])
def search():
    """
    Hybrid / single-method IR search.

    Request body:
      { "query": "...", "top_k": 10, "method": "hybrid", "cargo_type": "medicine" }

    Response:
      Evidence bundle with ranked results and per-score breakdown.
    """
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        return _err("'query' is required")

    top_k      = min(int(body.get("top_k", 10)), 50)
    method     = body.get("method", "hybrid")
    cargo_type = body.get("cargo_type")

    if method not in ("hybrid", "bm25", "tfidf", "dense"):
        return _err("method must be one of: hybrid, bm25, tfidf, dense")

    try:
        bundle = ir_engine.search(query, top_k=top_k, method=method, cargo_type=cargo_type)
        return jsonify({
            "status": "success",
            **bundle.to_dict(),
        })
    except Exception as e:
        logger.exception("Search failed: %s", e)
        return _err(f"Search failed: {e}", 500)


# ─────────────────────────────────────────────────────────────────
# POST /api/rag/query
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/rag/query", methods=["POST"])
def rag_query():
    """
    Full RAG pipeline: search → re-rank → route recommendation → grounded answer.

    Request body:
      {
        "query": "Can I transport medicine from Guwahati to Kolkata today?",
        "top_k": 10,
        "cargo_type": "medicine"
      }

    Response includes:
      - parsed query
      - expanded terms
      - evidence bundle
      - grounded answer
      - risk level
      - route recommendation (from existing LogiRush engine)
    """
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        return _err("'query' is required")

    top_k      = min(int(body.get("top_k", 10)), 50)
    cargo_type = body.get("cargo_type")
    method     = body.get("method", "hybrid")

    if method not in ("hybrid", "bm25", "tfidf", "dense"):
        method = "hybrid"

    try:
        # 1. Retrieve evidence using the requested method
        bundle = ir_engine.search(query, top_k=top_k, method=method, cargo_type=cargo_type)

        # 2. Generate grounded answer
        rag_result = generate_answer(bundle)

        # 3. Route recommendation — call existing engine if we have origin+dest
        route_rec = _route_recommendation(bundle, cargo_type)

        return jsonify({
            "status":            "success",
            "query":             query,
            "parsed_query":      bundle.parsed,
            "retrieval_method":  method,
            "latency_ms":        round(bundle.latency_ms, 1),
            "evidence":          bundle.to_dict()["results"],
            "answer":            rag_result["answer"],
            "risk_level":        rag_result["risk_level"],
            "grounded":          rag_result["grounded"],
            "provider":          rag_result.get("provider"),
            "evidence_used":     rag_result["evidence_used"],
            "note":              rag_result.get("note"),
            "route_recommendation": route_rec,
        })

    except Exception as e:
        logger.exception("RAG query failed: %s", e)
        return _err(f"RAG query failed: {e}", 500)


def _route_recommendation(bundle, cargo_type: str | None) -> dict | None:
    """
    Call the existing LogiRush route engine using IR-derived risk signals.

    If origin/destination are available from the parsed query, delegate to
    the NER router.  Returns None if insufficient location data.
    """
    parsed = bundle.parsed
    origin_name = parsed.get("origin")
    dest_name   = parsed.get("destination")

    if not origin_name or not dest_name:
        return {
            "available": False,
            "reason": "Origin or destination not identified in query. "
                      "Please specify locations explicitly for route planning.",
        }

    try:
        from src.services.routing_service import routing_service
        conditions = routing_service.get_conditions()
        graph = conditions.get("graph")

        if graph is None:
            return {"available": False, "reason": "Route graph not available."}

        # Resolve place names to location IDs in the existing network
        origin_id = _resolve_location_id(graph, origin_name)
        dest_id   = _resolve_location_id(graph, dest_name)

        if not origin_id or not dest_id:
            return {
                "available": False,
                "reason": (
                    f"The requested corridor ({origin_name} → {dest_name}) is outside "
                    "the currently indexed network. Route planning is available for "
                    "Northeast India. For other corridors, use the evidence above."
                ),
            }

        from src.optimization.ner_router import NERRouter, build_route_response
        from src.modeling.cargo_profiles import get_weights

        weights = get_weights(cargo_type or "general", parsed.get("urgency", "normal"))
        router  = NERRouter(graph, weights=weights)
        routes  = router.find_routes(origin_id, dest_id, max_routes=2)

        if not routes:
            return {"available": False, "reason": "No viable route found."}

        best = routes[0]
        return {
            "available":   True,
            "origin":      origin_name,
            "destination": dest_name,
            "cargo_type":  cargo_type or "general",
            "recommended_route": build_route_response(
                best, graph, cargo_type or "general", parsed.get("urgency", "normal"), rank=1
            ),
            "alternatives": [
                build_route_response(r, graph, cargo_type or "general",
                                     parsed.get("urgency", "normal"), rank=i + 1)
                for i, r in enumerate(routes[1:], start=1)
            ],
        }

    except Exception as e:
        logger.warning("Route recommendation failed: %s", e)
        return {"available": False, "reason": f"Route engine error: {e}"}


def _resolve_location_id(graph, place_name: str) -> str | None:
    """
    Find a graph node whose name partially matches place_name.
    Returns the node ID or None.
    """
    if not graph or not place_name:
        return None
    place_lower = place_name.lower()
    # Exact attribute match
    for node, data in graph.nodes(data=True):
        name = str(data.get("name", data.get("city", data.get("label", "")))).lower()
        if place_lower in name or name in place_lower:
            return node
        if node.lower() == place_lower:
            return node
    return None


# ─────────────────────────────────────────────────────────────────
# GET /api/search/<doc_id>
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/search/<doc_id>", methods=["GET"])
def get_document(doc_id: str):
    """Return a single document with full metadata."""
    doc = ir_engine.get_document(doc_id)
    if not doc:
        return _err(f"Document '{doc_id}' not found", 404)
    return jsonify({"status": "success", "document": doc.to_dict()})


# ─────────────────────────────────────────────────────────────────
# GET /api/ir/boolean?q=flood+AND+Assam
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/ir/boolean", methods=["GET"])
def boolean_query():
    """
    Boolean retrieval.

    ?q=flood AND Assam
    ?q=landslide OR rockfall
    ?q=cyclone NOT historical
    """
    q = (request.args.get("q") or "").strip()
    if not q:
        return _err("'q' parameter is required")

    docs = ir_engine.boolean_query(q)
    return jsonify({
        "status":  "success",
        "query":   q,
        "count":   len(docs),
        "results": [d.to_dict() for d in docs],
    })


# ─────────────────────────────────────────────────────────────────
# GET /api/ir/phrase?q=NH27+flooding
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/ir/phrase", methods=["GET"])
def phrase_search():
    """
    Exact phrase search — consecutive token sequence.

    ?q=NH27 flooding
    ?q=Brahmaputra overflow
    """
    q = (request.args.get("q") or "").strip()
    if not q:
        return _err("'q' parameter is required")

    ir_engine._ensure_built()
    results = ir_engine._index.phrase_search(q)
    return jsonify({
        "status":  "success",
        "phrase":  q,
        "count":   len(results),
        "results": [
            {
                "doc_id":          r["doc_id"],
                "match_count":     r["match_count"],
                "match_positions": r["match_positions"],
                "snippet":         r["snippet"],
                **r["document"].to_dict(),
            }
            for r in results
        ],
    })


# ─────────────────────────────────────────────────────────────────
# GET /api/ir/proximity?t1=flood&t2=Assam&window=10
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/ir/proximity", methods=["GET"])
def proximity_search():
    """
    Proximity search — two terms within N tokens of each other.

    ?t1=flood&t2=Guwahati&window=8
    """
    t1     = (request.args.get("t1") or "").strip()
    t2     = (request.args.get("t2") or "").strip()
    window = min(int(request.args.get("window", 10)), 50)

    if not t1 or not t2:
        return _err("'t1' and 't2' parameters are required")

    ir_engine._ensure_built()
    results = ir_engine._index.proximity_search(t1, t2, window=window)
    return jsonify({
        "status":  "success",
        "term1":   t1,
        "term2":   t2,
        "window":  window,
        "count":   len(results),
        "results": [
            {
                "doc_id":       r["doc_id"],
                "min_distance": r["min_distance"],
                "snippet":      r["snippet"],
                **r["document"].to_dict(),
            }
            for r in results
        ],
    })


# ─────────────────────────────────────────────────────────────────
# GET /api/ir/corpus  — browse all indexed documents
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/ir/corpus", methods=["GET"])
def corpus_browser():
    """
    Return all indexed documents with optional filtering.

    ?hazard=flood
    ?state=Assam
    ?provenance=SYNTHETIC
    ?severity=high
    """
    ir_engine._ensure_built()
    docs = ir_engine._index.all_documents()

    hazard     = (request.args.get("hazard")     or "").lower()
    state      = (request.args.get("state")      or "").lower()
    provenance = (request.args.get("provenance") or "").upper()
    severity   = (request.args.get("severity")   or "").lower()

    if hazard:
        docs = [d for d in docs if d.hazard.lower() == hazard]
    if state:
        docs = [d for d in docs if state in (d.state or "").lower()]
    if provenance:
        docs = [d for d in docs if d.provenance == provenance]
    if severity:
        docs = [d for d in docs if d.severity.lower() == severity]

    return jsonify({
        "status": "success",
        "total":  len(docs),
        "documents": [d.to_dict() for d in docs],
    })


# ─────────────────────────────────────────────────────────────────
# GET /api/evaluation/results?method=hybrid&k=5
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/evaluation/results", methods=["GET"])
def evaluation_results():
    """
    Run retrieval evaluation and return comparison table.

    ?method=hybrid   (or bm25 / tfidf / dense / all)
    ?k=5
    """
    method = request.args.get("method", "all")
    k      = min(int(request.args.get("k", 5)), 20)

    methods_to_run = ["tfidf", "bm25", "dense", "hybrid"] if method == "all" else [method]

    results = {}
    for m in methods_to_run:
        try:
            results[m] = ir_engine.evaluate(method=m, top_k=k)
        except Exception as e:
            logger.warning("Evaluation failed for %s: %s", m, e)
            results[m] = {"error": str(e)}

    # Build comparison table
    table = []
    for m, r in results.items():
        if "error" not in r:
            table.append({
                "method":        m,
                f"P@{k}":        r.get("mean_p_at_k"),
                f"Recall@{k}":   r.get("mean_recall_at_k"),
                f"F1@{k}":       r.get("mean_f1_at_k"),
                "MRR":           r.get("mrr"),
                "latency_ms":    r.get("mean_latency_ms"),
            })

    return jsonify({
        "status":           "success",
        "k":                k,
        "comparison_table": table,
        "details":          results,
    })


# ─────────────────────────────────────────────────────────────────
# GET /api/ir/status
# ─────────────────────────────────────────────────────────────────
@ir_bp.route("/ir/status", methods=["GET"])
def ir_status():
    return jsonify({
        "status":           "success",
        "documents_indexed": ir_engine.document_count,
        "dense_ready":      ir_engine._dense.is_ready if ir_engine._dense else False,
        "engine_built":     ir_engine._built,
    })
