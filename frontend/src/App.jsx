import React, { useState } from "react";
import { AreaChart } from "lucide-react";

import Connect from "./pages/Connect";
import Dashboard from "./pages/Dashboard";
import Report from "./pages/Report";

const views = {
  connect: "connect",
  dashboard: "dashboard",
  report: "report",
};

export default function App() {
  const [view, setView] = useState(views.connect);
  const [session, setSession] = useState({
    jobs: [],
    activeRunId: "",
  });

  const activeJob = session.jobs.find((job) => job.runId === session.activeRunId) || session.jobs[0] || null;
  const activeRunId = activeJob?.runId || "";

  return (
    <div className="app-shell">
      <div className="bg-orb orb-1" />
      <div className="bg-orb orb-2" />
      <header className="topbar reveal-1">
        <div className="brand">
          <span className="brand-icon">
            <AreaChart size={18} />
          </span>
          <div>
            <h1>PEIP</h1>
            <p>Predictive Engineering Impact Platform</p>
          </div>
        </div>
        <div className="topbar-right">
          {session.jobs.length > 1 && (
            <label className="run-switch">
              Active Repository
              <select
                value={activeRunId}
                onChange={(event) => {
                  setSession((current) => ({ ...current, activeRunId: event.target.value }));
                }}
              >
                {session.jobs.map((job) => (
                  <option key={job.runId} value={job.runId}>
                    {job.repoName}
                  </option>
                ))}
              </select>
            </label>
          )}
          {activeJob?.repoName && <div className="repo-chip">{activeJob.repoName}</div>}
        </div>
      </header>

      <main className="content">
        {view === views.connect && (
          <Connect
            onStarted={(next) => {
              setSession({
                jobs: next.jobs,
                activeRunId: next.activeRunId || next.jobs[0]?.runId || "",
              });
              setView(views.dashboard);
            }}
          />
        )}

        {view === views.dashboard && activeRunId && (
          <Dashboard
            runId={activeRunId}
            repoName={activeJob?.repoName || ""}
            onOpenReport={() => {
              setView(views.report);
            }}
          />
        )}

        {view === views.report && activeRunId && (
          <Report
            runId={activeRunId}
            repoName={activeJob?.repoName || ""}
            onBack={() => {
              setView(views.dashboard);
            }}
          />
        )}
      </main>
    </div>
  );
}
