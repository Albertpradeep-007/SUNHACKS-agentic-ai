import json
import os

def generate_dashboard(scores_file, output_html):
    with open(scores_file, 'r') as f:
        scores = json.load(f)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PEIP Engineering Intelligence Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }}
            .container {{ max-width: 1200px; margin: auto; }}
            h1 {{ font-size: 2.5em; text-align: center; margin-bottom: 40px; color: #38bdf8; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-5px); border-color: #38bdf8; }}
            .repo-name {{ font-size: 1.25em; font-weight: bold; margin-bottom: 10px; color: #e2e8f0; }}
            .score-circle {{ width: 80px; height: 80px; border-radius: 50%; border: 4px solid #38bdf8; display: flex; align-items: center; justify-content: center; font-size: 1.5em; font-weight: bold; margin: 15px 0; }}
            .metrics {{ font-size: 0.9em; color: #94a3b8; }}
            .metric {{ display: flex; justify-content: space-between; margin-bottom: 5px; }}
            .status-low {{ border-color: #ef4444; color: #ef4444; }}
            .status-med {{ border-color: #fbbf24; color: #fbbf24; }}
            .status-high {{ border-color: #22c55e; color: #22c55e; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Predictive Engineering Intelligence Portfolio</h1>
            <div class="grid">
    """
    
    for s in scores:
        status_class = "status-high" if s['final_health_score'] >= 75 else ("status-med" if s['final_health_score'] >= 50 else "status-low")
        html += f"""
                <div class="card">
                    <div class="repo-name">{s['repo']}</div>
                    <div class="score-circle {status_class}">{s['final_health_score']}</div>
                    <div class="metrics">
                        <div class="metric"><span>Stability</span><span>{s['scores']['stability']}%</span></div>
                        <div class="metric"><span>Complexity</span><span>{s['scores']['complexity']}%</span></div>
                        <div class="metric"><span>Maintainability</span><span>{s['scores']['maintainability']}%</span></div>
                        <div class="metric"><span>Risk Profile</span><span>{s['scores']['risk']}%</span></div>
                    </div>
                </div>
        """
        
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(output_html, 'w') as f:
        f.write(html)
    print(f"Generated {output_html}")

if __name__ == "__main__":
    generate_dashboard("reports/health_scores.json", "reports/summary_dashboard.html")
