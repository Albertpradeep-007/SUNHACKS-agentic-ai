import React from "react";

const ENGINEER_HOURLY = 75;

export default function CostCard({ predictions }) {
  const totalHours = (predictions || []).reduce((sum, item) => sum + (item.remediation_hours || 0), 0);
  const highUrgencyCount = (predictions || []).filter((item) => item.urgency === "high").length;
  const projectedIncidentCost = highUrgencyCount * 8 * ENGINEER_HOURLY;

  return (
    <div className="panel cost-card">
      <div className="panel-header">
        <h3>Cost Snapshot</h3>
      </div>
      <div className="cost-metric-row">
        <div>
          <p className="label">Total remediation effort</p>
          <p className="value">{totalHours}h</p>
        </div>
        <div>
          <p className="label">Incident exposure</p>
          <p className="value">${projectedIncidentCost.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
