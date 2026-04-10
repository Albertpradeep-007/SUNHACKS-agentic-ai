import React, { useEffect, useState } from "react";
import { Download, ScrollText } from "lucide-react";

import { getReportMarkdown, reportHtmlUrl, reportUrl } from "../api";

export default function Report({ runId, repoName, onBack }) {
  const [markdown, setMarkdown] = useState("Loading report preview...");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getReportMarkdown(runId);
        setMarkdown(res.data);
      } catch (_err) {
        setMarkdown("Report markdown is not ready yet. Download PDF once generation completes.");
      }
    };
    load();
  }, [runId]);

  return (
    <section className="panel reveal-3">
      <div className="panel-header report-head">
        <div>
          <h2>CEO Report</h2>
          <p>
            Executive summary and risk impact narrative.
            {repoName ? ` Active repository: ${repoName}.` : ""}
          </p>
        </div>
        <div className="report-actions">
          <a className="btn" href={reportUrl(runId)} target="_blank" rel="noreferrer">
            <Download size={16} />
            Download PDF
          </a>
          <a className="btn ghost" href={reportHtmlUrl(runId)} target="_blank" rel="noreferrer">
            Open HTML
          </a>
          <button type="button" className="btn ghost" onClick={onBack}>
            Back to Dashboard
          </button>
        </div>
      </div>
      <div className="markdown-preview">
        <div className="preview-title">
          <ScrollText size={16} />
          Markdown Preview
        </div>
        <pre>{markdown}</pre>
      </div>
    </section>
  );
}
