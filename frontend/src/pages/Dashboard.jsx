import React, { useEffect, useMemo, useState } from "react";
import { Activity, FileWarning, RefreshCw } from "lucide-react";

import { getResults } from "../api";
import CostCard from "../components/CostCard";
import HealthHeatmap from "../components/HealthHeatmap";
import RiskTable from "../components/RiskTable";

export default function Dashboard({ runId, repoName, onOpenReport }) {
  const [status, setStatus] = useState("pending");
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const res = await getResults(runId);
        if (!alive) {
          return;
        }
        setStatus(res.data.status);
        setPayload(res.data);
        if (res.data.status === "error") {
          setError(res.data.error || "Analysis failed");
        }
      } catch (err) {
        if (alive) {
          setError(err?.response?.data?.detail || "Failed to fetch run status");
        }
      }
    };

    poll();
    const timer = setInterval(poll, 3000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [runId]);

  const ready = status === "done";
  const healthScores = payload?.health_scores || [];
  const predictions = payload?.predictions || [];
  const topRiskCount = useMemo(() => predictions.filter((item) => item.urgency === "high").length, [predictions]);

  return (
    <section className="reveal-2">
      <div className="hero-strip panel">
        <div>
          <h2>Analysis Dashboard</h2>
          {repoName && <p>Repository: {repoName}</p>}
          <p>Run ID: {runId}</p>
        </div>
        <div className="status-box">
          <RefreshCw size={16} className={status === "running" ? "spin" : ""} />
          <span>Status: {status}</span>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {!ready && (
        <div className="panel loading-panel">
          <Activity size={18} />
          <p>Mining commits, scoring health, predicting risk, and writing report...</p>
        </div>
      )}

      {ready && (
        <>
          <div className="kpi-grid">
            <div className="panel kpi-card">
              <p className="label">Scored Modules</p>
              <p className="value">{healthScores.length}</p>
            </div>
            <div className="panel kpi-card">
              <p className="label">Predicted Risks</p>
              <p className="value">{predictions.length}</p>
            </div>
            <div className="panel kpi-card">
              <p className="label">High-Urgency Risks</p>
              <p className="value">{topRiskCount}</p>
            </div>
          </div>

          <HealthHeatmap healthScores={healthScores} />
          <CostCard predictions={predictions} />
          <RiskTable predictions={predictions} />

          <button type="button" className="btn wide" onClick={onOpenReport}>
            <FileWarning size={16} />
            Open CEO Report
          </button>
        </>
      )}
    </section>
  );
}
