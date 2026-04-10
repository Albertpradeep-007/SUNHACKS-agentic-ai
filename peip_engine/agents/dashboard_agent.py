"""
DashboardAgent — PEIP Output HTML Renderer
Generates a stunning, interactive local HTML Dashboard with Chart.js,
and embeds exact bug and crash predictions from Ollama.
"""

import json
import os

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PEIP | Predictive Engineering Intelligence</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css" rel="stylesheet">
    <style>
        :root {
            --bg: #020617;
            --card-bg: #0f172a;
            --border: #1e293b;
            --accent: #38bdf8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: #f8fafc;
            margin: 0;
            padding: 2rem;
            line-height: 1.5;
        }

        .nav-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1rem;
        }

        .nav-header h1 {
            font-size: 1.5rem;
            margin: 0;
            font-weight: 800;
            letter-spacing: -0.05em;
            color: var(--accent);
        }

        .badge-live {
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            padding: 4px 12px;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
        }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--card-bg);
            padding: 1.25rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .stat-card label {
            display: block;
            color: #94a3b8;
            font-size: 0.75rem;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .stat-card .value {
            font-size: 1.5rem;
            font-weight: 700;
        }

        .main-layout {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
        }

        .card {
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 1.5rem;
        }

        .card h2 {
            font-size: 1rem;
            color: #94a3b8;
            margin-top: 0;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.75rem;
        }

        .prediction-box {
            background: #020617;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
            border: 1px solid #334155;
        }

        .prediction-header {
            display: flex;
            align-items: center;
            color: var(--accent);
            font-weight: bold;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }

        pre {
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            color: #cbd5e1;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .btn-action {
            background: var(--accent);
            color: #000;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.8rem;
            margin-top: 1rem;
        }

        .chart-container {
            height: 200px;
            width: 100%;
            position: relative;
        }

        /* Timeline CSS */
        .timeline {
            border-left: 2px solid var(--border);
            padding-left: 1rem;
            margin-top: 1rem;
        }
        .timeline-item {
            position: relative;
            margin-bottom: 1rem;
        }
        .timeline-item::before {
            content: "";
            position: absolute;
            width: 10px;
            height: 10px;
            background: var(--accent);
            border-radius: 50%;
            left: -1.4rem;
            top: 4px;
        }
        .timeline-item .time {
            font-size: 0.7rem;
            color: #64748b;
        }
        .timeline-item .message {
            font-size: 0.85rem;
            color: #cbd5e1;
        }
        .diff-code {
            max-height: 250px; 
            overflow: auto; 
            padding: 1rem; 
            font-family: monospace; 
            font-size: 0.8rem; 
            border-radius: 4px;
        }
    </style>
</head>
<body>

    <div class="nav-header">
        <h1>PEIP <span style="color:white">/ TEAM WAR ROOM</span></h1>
        <div class="badge-live">● System Live: Ollama LLaMa3 Connected</div>
    </div>

    <!-- ROI Calculator Header -->
    <div class="stat-grid" id="roiGrid">
        <div class="stat-card">
            <label>Portfolio Health</label>
            <div class="value" style="color: var(--danger)">At Risk</div>
        </div>
        <div class="stat-card">
            <label>Avg. Complexity (CC)</label>
            <div class="value" id="valCC">13.0</div>
        </div>
        <div class="stat-card">
            <label>Calculated ROI Saving</label>
            <div class="value" id="valROI" style="color: var(--success)">₹0</div>
        </div>
        <div class="stat-card">
            <label>DORA Score</label>
            <div class="value" style="color: var(--warning)">Low</div>
        </div>
    </div>

    <div class="main-layout">
        <div class="left-col">
            <div class="card">
                <h2>Vulnerability Predictions & AI Auto-Patches</h2>
                <div id="repoGrid"></div>
            </div>

            <div class="card">
                <h2>Complexity Heatmap (by File)</h2>
                <div class="chart-container">
                    <canvas id="complexityChart"></canvas>
                </div>
            </div>
        </div>

        <div class="right-col">
            <div class="card">
                <h2>Executive Assessment</h2>
                <div id="ceoReport" style="font-size: 0.9rem; color: #e2e8f0;"></div>
            </div>
            <div class="card">
                <h2>Pipeline Timeline</h2>
                <div class="timeline" id="timelineLog"></div>
            </div>
        </div>
    </div>

    <script>
        const data = __PAYLOAD__;

        const hrRate = 2500;
        let totalCC = 0;
        let cfsLength = 0;

        // Render Report
        document.getElementById('ceoReport').innerHTML = marked.parse(data.ceo_report || 'No report found.');
        
        // Render Repository Cards & Diffs
        const grid = document.getElementById('repoGrid');
        
        const labels = [];
        const ccData = [];
        const bgColors = [];

        data.repos_analyzed.forEach(repo => {
            const risk = data.risk_flags[repo] || {};
            const bp = data.bug_predictions[repo] || {};
            const patches = data.patches && data.patches[repo] ? data.patches[repo] : [];
            
            // For ROI graph
            if (data.complexity && data.complexity[repo] && data.complexity[repo].files) {
                const fls = data.complexity[repo].files;
                for (const path in fls) {
                    labels.push(path.split(/[\\\\/]/).pop());
                    ccData.push(fls[path].cc_max);
                    bgColors.push(fls[path].cc_grade >= 'C' ? '#ef4444' : '#38bdf8');
                    totalCC += fls[path].cc_max;
                    cfsLength++;
                }
            }

            let cardHtml = `
                <div style="margin-bottom: 2rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center">
                        <h3 style="margin:0; font-size: 1.2rem;">${repo}</h3>
                        <span class="badge-live" style="background: rgba(239, 68, 68, 0.1); color: var(--danger)">Status: ${risk.repo_classification || 'UNKNOWN'}</span>
                    </div>
                    <p style="color:#94a3b8; font-size: 0.85rem;">Primary Risk: ${risk.primary_signal || 'N/A'}</p>
            `;

            if (bp.predictions) {
                cardHtml += `
                    <div class="prediction-box">
                        <div class="prediction-header">
                            <i class="lucide-bot" style="margin-right:8px"></i> AI CRASH PREDICTION
                        </div>
                        <pre>${bp.predictions}</pre>
                    </div>`;
            }

            if (patches.length > 0) {
                const patch = patches[0];
                cardHtml += `
                    <div class="prediction-box" style="margin-top:1rem; border-left-color:var(--success);">
                        <div class="prediction-header" style="color:var(--success);">
                            <i class="lucide-check" style="margin-right:8px"></i> AUTO-PATCH DIFF: <span style="margin-left: 0.5rem; color: #cbd5e1;">${patch.file}</span>
                        </div>
                        <div style="display:flex; gap:1rem; margin-top: 1rem;">
                            <div style="flex:1;">
                                <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:0.5rem;">BEFORE (Grade ${patch.original_grade})</div>
                                <pre class="diff-code" style="background:#2C161D; border: 1px solid #7F1D1D;">${patch.original_content ? patch.original_content.replace(/</g, "&lt;").replace(/>/g, "&gt;") : "N/A"}</pre>
                            </div>
                            <div style="flex:1;">
                                <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:0.5rem;">AFTER (Status: ${patch.validation_status})</div>
                                <pre class="diff-code" style="background:#0F291E; border: 1px solid #065F46;">${patch.patched_content ? patch.patched_content.replace(/</g, "&lt;").replace(/>/g, "&gt;") : "N/A"}</pre>
                            </div>
                        </div>
                        <button class="btn-action" style="margin-top:1rem; background:var(--success); color:#fff;" onclick="alert('Creating Git Branch & Pull Request...')">
                            Commit Patch & Open PR
                        </button>
                    </div>
                `;
            }

            cardHtml += `</div>`;
            grid.innerHTML += cardHtml;
        });

        // ROI Calculator values
        const avgCC = cfsLength > 0 ? (totalCC / cfsLength).toFixed(1) : 0;
        document.getElementById('valCC').innerText = avgCC;
        
        // Return On Investment: (AvgCC * 0.5 hrs) * hourly_rate
        const roi = (avgCC * 0.5) * hrRate;
        document.getElementById('valROI').innerText = "₹" + Math.round(roi).toLocaleString();

        // Chart
        if(document.getElementById('complexityChart')) {
            const ctx = document.getElementById('complexityChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Cyclomatic Complexity',
                        data: ccData,
                        backgroundColor: bgColors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#1e293b' } },
                        x: { grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // Timeline
        if(data.pipeline_log) {
            const tl = document.getElementById('timelineLog');
            data.pipeline_log.forEach(log => {
                const date = new Date(log.ts);
                const timeStr = date.getHours().toString().padStart(2, '0') + ":" + 
                                date.getMinutes().toString().padStart(2, '0') + ":" + 
                                date.getSeconds().toString().padStart(2, '0');
                let clr = '#cbd5e1';
                if(log.level === 'WARN') clr = '#f59e0b';
                else if(log.level === 'TRANSITION') clr = '#38bdf8';
                
                tl.innerHTML += `
                <div class="timeline-item">
                    <div class="time">${timeStr} <span style="color: ${clr}; font-weight: bold; margin-left:8px;">[${log.level}]</span></div>
                    <div class="message">${log.message}</div>
                </div>`;
            });
        }

    </script>
</body>
</html>
'''

def render_dashboard(final_output: dict) -> None:
    # 1. Provide Context for patches (Load Original & Patched text strings into the JSON)
    base_repo_path = "peip_workspace"
    peip_patches = final_output.get("patches", {})
    for repo, patch_list in peip_patches.items():
        for p in patch_list:
            original_file = os.path.join(base_repo_path, repo, p.get("file", ""))
            try:
                with open(original_file, "r", encoding="utf-8") as f:
                    p["original_content"] = f.read()
            except Exception:
                p["original_content"] = "Could not load original source."
                
            try:
                with open(p.get("patch_path", ""), "r", encoding="utf-8") as f:
                    p["patched_content"] = f.read()
            except Exception:
                p["patched_content"] = "Could not load patched source."

    print("\n" + "="*64)
    print("  PEIP INTERACTIVE REPORT PIPELINE COMPLETED")
    print("="*64)
    for r in final_output.get("repos_analyzed", []):
        risk = final_output.get("risk_flags", {}).get(r, {}).get("repo_classification", "UNKNOWN")
        print(f"  > {r}: {risk}")
        
    print("\n  Generating HTML Interactive Dashboard...")

    json_payload = json.dumps(final_output)
    html_content = HTML_TEMPLATE.replace("__PAYLOAD__", json_payload)
    
    os.makedirs("reports", exist_ok=True)
    out_path = os.path.join("reports", "peip_interactive_report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"  [OK] Interactive HTML Report saved to: {out_path}")
    print("="*64 + "\n")

if __name__ == "__main__":
    scores_path = os.path.join(os.getcwd(), "peip_pipeline_output.json")
    if not os.path.exists(scores_path):
        print("ERROR: peip_pipeline_output.json not found.")
    else:
        with open(scores_path, encoding="utf-8") as f:
            data = json.load(f)
        render_dashboard(data)

