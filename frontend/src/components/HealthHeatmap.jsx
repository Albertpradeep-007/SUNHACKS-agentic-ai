import React from "react";
import { ResponsiveContainer, Tooltip, Treemap } from "recharts";

const TIER_COLOR = {
  green: "#2f9f61",
  yellow: "#d89c1f",
  red: "#d6554f",
};

function tileRenderer(props) {
  const { x, y, width, height, name, fill } = props;
  if (width < 40 || height < 30) {
    return <rect x={x} y={y} width={width} height={height} fill={fill} stroke="#ffffff" strokeWidth={2} />;
  }
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={fill} stroke="#ffffff" strokeWidth={2} />
      <text x={x + 8} y={y + 18} fontSize={12} fill="#fff9ef" fontWeight={700}>
        {name}
      </text>
    </g>
  );
}

export default function HealthHeatmap({ healthScores }) {
  const data = (healthScores || []).map((row) => ({
    name: row.module?.split("/").pop() || row.module,
    size: (row.churn || 0) + 1,
    fill: TIER_COLOR[row.tier] || "#7a8894",
    score: row.score,
    tier: row.tier,
    module: row.module,
  }));

  return (
    <div className="panel heatmap-panel">
      <div className="panel-header">
        <h3>Module Health Heatmap</h3>
        <p>Tile size is churn, color is risk tier.</p>
      </div>
      <div className="heatmap-wrap">
        <ResponsiveContainer width="100%" height={350}>
          <Treemap
            data={data}
            dataKey="size"
            stroke="#ffffff"
            fill="#0f4f66"
            content={tileRenderer}
            animationDuration={700}
          >
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #c6d6de",
                fontFamily: "Space Grotesk, sans-serif",
              }}
              formatter={(value, _name, payload) => [value, `Churn (${payload.payload.module})`]}
            />
          </Treemap>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
