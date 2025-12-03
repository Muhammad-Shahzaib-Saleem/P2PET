import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Label } from "recharts";

// NOTE: keep this import exactly as you already have it working.
// If your theme is in src/components/shared/, and THIS file is in
// src/components/Energy/ChartsTabs/, the path is "../../shared/chartTheme".
import { ENERGY_COLORS } from "../shared/chartTheme";

/* --- Y domain with guaranteed headroom for the inside legend --- */
const yDomainWithHeadroom = (
  rows = [], k1, k2,
  topPadRatio = 0.30, minTopPad = 4.5, extraTopPad = 0.6
) => {
  let maxVal = 0;
  for (const r of rows) {
    const a = Number(r?.[k1]) || 0;
    const b = Number(r?.[k2]) || 0;
    if (a > maxVal) maxVal = a;
    if (b > maxVal) maxVal = b;
  }
  if (maxVal <= 0) return [0, 1];
  const pad = Math.max(maxVal * topPadRatio, minTopPad) + extraTopPad;
  return [0, maxVal + pad];
};

const EnergyDualBar = ({ data = [], xLabel = "Day", onSelectItem }) => {
  const isMobile = typeof window !== "undefined" && window.matchMedia("(max-width: 600px)").matches;
  const MARGIN = isMobile ? { top: 8, right: 8, bottom: 18, left: 6 } : { top: 16, right: 12, bottom: 36, left: 30 };
  const yAxisWidth = isMobile ? 26 : 34;
  const barGap = isMobile ? 10 : 18;
  const tickStyle = { fill: "#374151", fontSize: isMobile ? 10 : 12 };

  const [yMin, yMax] = yDomainWithHeadroom(data, "importKwh", "exportKwh", 0.30, 4);

  // If parent provides onSelectItem, clicking a bar will call it with the row.
  const handleClick = (_evt, index) => {
    if (!onSelectItem) return;
    const row = data?.[index];
    if (row) onSelectItem(row);
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {/* INSIDE legend: top-right of plotting area */}
      <div
        style={{
          position: "absolute",
          top: MARGIN.top + 4,
          right: MARGIN.right + 4,
          background: "rgba(255,255,255,0.9)",
          border: "1px solid #e5e7eb",
          borderRadius: 10,
          padding: isMobile ? "4px 6px" : "6px 8px",
          lineHeight: 1.1,
          fontSize: isMobile ? 11 : 12,
          pointerEvents: "none",
          zIndex: 1,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "2px 0" }}>
          <span style={{ width: 10, height: 10, borderRadius: 999, background: ENERGY_COLORS.export }} />
          <span>Export kWh</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "2px 0" }}>
          <span style={{ width: 10, height: 10, borderRadius: 999, background: ENERGY_COLORS.import }} />
          <span>Import kWh</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={MARGIN} barCategoryGap={barGap}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="t" tick={tickStyle} tickMargin={4}>
            {/* keep x label on desktop, remove on phones to reclaim height */}
            {!isMobile && (
              <Label value={xLabel} position="insideBottom" dy={14} fill="#111827" />
            )}
          </XAxis>
          <YAxis domain={[yMin, yMax]} width={yAxisWidth} tickMargin={6} tick={tickStyle}>
            {!isMobile && (
              <Label
                value="Energy (kWh)"
                angle={-90}
                position="left"
                offset={18}
                style={{ textAnchor: "middle" }}
                fill="#111827"
              />
            )}
          </YAxis>

          <Tooltip formatter={(v, n) => [`${Number(v ?? 0).toFixed(2)} kWh`, n]}
          wrapperStyle={{ fontSize: isMobile ? 12 : 13 }}
          />

          {/* Click any bar → parent gets the row */}
          <Bar dataKey="importKwh" name="Import kWh" fill={ENERGY_COLORS.import}
               radius={[6, 6, 0, 0]} onClick={handleClick} />
          <Bar dataKey="exportKwh" name="Export kWh" fill={ENERGY_COLORS.export}
               radius={[6, 6, 0, 0]} onClick={handleClick} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EnergyDualBar;
