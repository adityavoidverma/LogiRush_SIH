import { Link } from "react-router-dom";

const Home = () => {
  return (
    <div className="max-w-[1600px] mx-auto px-4 py-12">
      <div className="text-center mb-16">
        <h1 className="text-3xl md:text-4xl font-semibold mb-4 text-ink tracking-tight">
          LogiRush
        </h1>
        <p className="text-xl text-ink-secondary max-w-3xl mx-auto mb-2">
          Pan-India Multi-Hazard Logistics Intelligence Search
        </p>
        <p className="text-sm text-ink-secondary max-w-xl mx-auto">
          Hybrid IR · Dense Retrieval · RAG · Multi-Hazard Intelligence · Geographic Relevance · Risk-Aware Routing
        </p>
      </div>

      {/* Primary CTA */}
      <div className="bg-surface border border-accent/30 rounded-xl p-8 mb-8 text-center">
        <h2 className="text-2xl font-semibold mb-3 text-accent">Intelligence Search</h2>
        <p className="text-ink-secondary mb-5 max-w-lg mx-auto">
          Search the risks, retrieve the evidence, understand the disruption, and choose the safer route.
        </p>
        <Link
          to="/search"
          className="inline-block px-8 py-3 bg-accent rounded-lg hover:brightness-110 transition-all font-semibold text-lg"
          style={{ color: 'var(--bg-contrast)' }}
        >
          Open Search →
        </Link>
      </div>

      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <div className="bg-surface border border-white/10 rounded-lg p-8 hover:border-accent transition-colors">
          <h2 className="text-2xl font-semibold mb-4 text-accent">
            Disaster-Resilient Routing
          </h2>
          <p className="text-ink-secondary mb-6">
            Advanced route optimization for the North Eastern Region with real-time disaster
            prediction and accessibility scoring.
          </p>
          <Link
            to="/shipment-planner"
            className="inline-block px-6 py-3 bg-accent rounded-lg hover:brightness-110 transition-all font-semibold"
            style={{ color: 'var(--bg-contrast)' }}
          >
            Plan Shipment
          </Link>
        </div>

        <div className="bg-surface border border-white/10 rounded-lg p-8 hover:border-accent transition-colors">
          <h2 className="text-2xl font-semibold mb-4 text-accent">
            Accessibility Intelligence
          </h2>
          <p className="text-ink-secondary mb-6">
            Real-time road condition monitoring, incident tracking, and accessibility scoring
            for informed decision-making.
          </p>
          <Link
            to="/accessibility-map"
            className="inline-block px-6 py-3 bg-accent rounded-lg hover:brightness-110 transition-all font-semibold"
            style={{ color: 'var(--bg-contrast)' }}
          >
            View Map
          </Link>
        </div>
      </div>

      <div className="bg-surface border border-white/10 rounded-lg p-8">
        <h2 className="text-2xl font-semibold mb-6">What Makes LogiRush Different</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-lg font-medium mb-2 text-accent">Hybrid IR</h3>
            <p className="text-ink-secondary text-sm">
              BM25 + semantic embeddings + freshness + geographic relevance + source authority — fused into one ranked evidence list.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2 text-accent">Grounded Answers</h3>
            <p className="text-ink-secondary text-sm">
              Route-risk answers are grounded in retrieved evidence. Every claim cites a document. No invented road closures.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2 text-accent">Explainable Ranking</h3>
            <p className="text-ink-secondary text-sm">
              Click "Why ranked #1?" on any result to see every contributing score broken down transparently.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2 text-accent">Risk-Aware Routing</h3>
            <p className="text-ink-secondary text-sm">
              Multi-objective path finding considering time, cost, accessibility, and disaster risk.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2 text-accent">Disaster Prediction</h3>
            <p className="text-ink-secondary text-sm">
              ML-based disruption probability for road segments using historical and live data.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2 text-accent">IR Evaluation</h3>
            <p className="text-ink-secondary text-sm">
              Live P@K, Recall@K, MRR comparison across TF-IDF, BM25, dense and hybrid — measured, not claimed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
