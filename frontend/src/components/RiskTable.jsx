import React from "react";

const urgencyClass = {
  high: "pill danger",
  medium: "pill warning",
  low: "pill safe",
};

export default function RiskTable({ predictions }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Predicted Failure Risks (90 Days)</h3>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Module</th>
              <th>Risk</th>
              <th>Type</th>
              <th>Remediation Hours</th>
              <th>Urgency</th>
            </tr>
          </thead>
          <tbody>
            {(predictions || []).map((item) => (
              <tr key={item.module}>
                <td>{item.module}</td>
                <td>{Math.round((item.risk_probability || 0) * 100)}%</td>
                <td>{item.predicted_failure_type || "stability risk"}</td>
                <td>{item.remediation_hours || 0}</td>
                <td>
                  <span className={urgencyClass[item.urgency] || "pill"}>{item.urgency || "medium"}</span>
                </td>
              </tr>
            ))}
            {(!predictions || predictions.length === 0) && (
              <tr>
                <td colSpan={5}>No elevated risks detected yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
