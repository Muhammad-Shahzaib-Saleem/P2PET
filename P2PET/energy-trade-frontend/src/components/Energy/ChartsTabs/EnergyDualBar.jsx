import React from "react";
import {
  ResponsiveContainer,
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Label
} from "recharts";
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

const MARGIN = { top: 16, right: 12, bottom: 36, left: 30 };

const EnergyDualBar = ({ data = [], xLabel = "Day", onSelectItem }) => {
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
          padding: "6px 8px",
          lineHeight: 1.1,
          fontSize: 12,
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
        <BarChart data={data} margin={MARGIN} barCategoryGap={18}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="t">
            <Label value={xLabel} position="insideBottom" dy={14} fill="#111827" />
          </XAxis>
          <YAxis domain={[yMin, yMax]} tickMargin={6} tick={{ fill: "#374151" }}>
            <Label
              value="Energy (kWh)"
              angle={-90}
              position="left"
              offset={18}
              style={{ textAnchor: "middle" }}
              fill="#111827"
            />
          </YAxis>

          <Tooltip formatter={(v, n) => [`${Number(v ?? 0).toFixed(2)} kWh`, n]} />

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



// import React from "react";
// import {
//   ResponsiveContainer,
//   BarChart, Bar,
//   XAxis, YAxis, CartesianGrid, Tooltip, Label
// } from "recharts";
// import { ENERGY_COLORS } from "../shared/chartTheme";

// /* --- Y domain with guaranteed headroom for the inside legend --- */
// /* Adds a % of the tallest bar (topPadRatio) but at least minTopPad kWh */
// const yDomainWithHeadroom = (rows = [], k1, k2, topPadRatio = 0.30, minTopPad = 4.5, extraTopPad = 0.6) => {
//   let maxVal = 0;
//   for (const r of rows) {
//     const a = Number(r?.[k1]) || 0;
//     const b = Number(r?.[k2]) || 0;
//     if (a > maxVal) maxVal = a;
//     if (b > maxVal) maxVal = b;
//   }
//   if (maxVal <= 0) return [0, 1];
//   const pad = Math.max(maxVal * topPadRatio, minTopPad) + extraTopPad;
//   return [0, maxVal + pad];
// };

// const MARGIN = { top: 16, right: 12, bottom: 36, left: 30 };

// const EnergyDualBar = ({ data = [] }) => {
//   const [yMin, yMax] = yDomainWithHeadroom(data, "importKwh", "exportKwh", 0.30, 4);

//   return (
//     <div style={{ position: "relative", width: "100%", height: "100%" }}>
//       {/* INSIDE legend: top-right of plotting area */}
//       <div
//         style={{
//           position: "absolute",
//           top: MARGIN.top + 4,
//           right: MARGIN.right + 4,
//           background: "rgba(255,255,255,0.9)",
//           border: "1px solid #e5e7eb",
//           borderRadius: 10,
//           padding: "6px 8px",
//           lineHeight: 1.1,
//           fontSize: 12,
//           pointerEvents: "none",
//           zIndex: 1,
//         }}
//       >
//         <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "2px 0" }}>
//           <span style={{ width: 10, height: 10, borderRadius: 999, background: ENERGY_COLORS.export }} />
//           <span>Export kWh</span>
//         </div>
//         <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "2px 0" }}>
//           <span style={{ width: 10, height: 10, borderRadius: 999, background: ENERGY_COLORS.import }} />
//           <span>Import kWh</span>
//         </div>
//       </div>

//       <ResponsiveContainer width="100%" height="100%">
//         <BarChart data={data} margin={MARGIN} barCategoryGap={18}>
//           <CartesianGrid strokeDasharray="3 3" />
//           <XAxis dataKey="t">
//             <Label value="Day" position="insideBottom" dy={14} fill="#111827" />
//           </XAxis>
//           <YAxis domain={[yMin, yMax]} tickMargin={6} tick={{ fill: "#374151" }}>
//             <Label
//               value="Energy (kWh)"
//               angle={-90}
//               position="left"
//               offset={18}
//               style={{ textAnchor: "middle" }}
//               fill="#111827"
//             />
//           </YAxis>

//           <Tooltip formatter={(v, n) => [`${Number(v ?? 0).toFixed(2)} kWh`, n]} />

//           <Bar dataKey="importKwh" name="Import kWh" fill={ENERGY_COLORS.import} radius={[6, 6, 0, 0]} />
//           <Bar dataKey="exportKwh" name="Export kWh" fill={ENERGY_COLORS.export} radius={[6, 6, 0, 0]} />
//         </BarChart>
//       </ResponsiveContainer>
//     </div>
//   );
// };

// export default EnergyDualBar;
