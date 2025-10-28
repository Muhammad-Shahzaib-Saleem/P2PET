import React from "react";
import {
  ResponsiveContainer,
  LineChart, Line,
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Label
} from "recharts";

const DEFAULT_MARGIN = { top: 12, right: 16, bottom: 14, left: 24 };
const Y_LABEL_OFFSET = 18;

const paddedDomain = (data, key, padPct = 0.08) => {
  if (!data || !data.length) return ["auto", "auto"];
  let min = Infinity, max = -Infinity;
  for (const d of data) {
    const v = Number(d?.[key]);
    if (Number.isFinite(v)) { if (v < min) min = v; if (v > max) max = v; }
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) return ["auto", "auto"];
  const range = Math.max(1e-6, max - min);
  const pad = range * padPct;
  return [min - pad, max + pad];
};

const estimateYWidthFromDomain = (min, max, decimals = 2) => {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return 50;
  const s1 = min.toFixed(decimals);
  const s2 = max.toFixed(decimals);
  const longest = Math.max(s1.length, s2.length);
  return Math.min(96, Math.max(44, longest * 8 + 14));
};

const ChartBase = ({
  chart = "line",
  data = [],
  xKey = "t",
  yKey,
  xLabel = "Time",
  yLabel,
  color = "#4f46e5",
  decimals = 2,
  yPadPct = 0.08,
  yTicks,
  yTickFormatter,
  tooltipFormatter,

  /* numeric x-axis controls */
  xType = "category",
  xDomain,
  xTicks,
  xTickFormatter,
  tooltipLabelFormatter,

  /* line dot controls */
  lineDot = false,
  lineActiveDot = { r: 4 },

  /* mobile-aware knobs */
  margins = DEFAULT_MARGIN,
  tickFont = 12,
  axisLabelFont = 12,
  showAxisLabels = true,
  yAxisMinWidth = 44,
  compact = false,  // when true (mobile), we want a skinny left side but KEEP ticks
}) => {
  const [min, max] = paddedDomain(data, yKey, yPadPct);

  // KEY CHANGE: on compact (mobile), force a skinny axis column.
  const estimated = estimateYWidthFromDomain(min, max, decimals);
  const yWidth = compact ? yAxisMinWidth : Math.max(yAxisMinWidth, estimated);

  const tickStyle = { fill: "#374151", fontSize: tickFont };
  const xTickProp = tickStyle; // optional: hide dense x ticks on very small screens
  const yTickProp = tickStyle;                   // keep Y ticks visible

  const Axes = () => (
    <>
      <CartesianGrid strokeDasharray="3 3" />

      <XAxis
        dataKey={xKey}
        type={xType}
        domain={xDomain}
        ticks={xTicks}
        tickFormatter={xTickFormatter}
        tick={xTickProp}
        tickMargin={compact ? 2 : 4}
        axisLine={!compact}
        tickLine={!compact}
      >
        {showAxisLabels && xLabel && (
          <Label
            value={xLabel}
            position="insideBottom"
            dy={12}
            style={{ fontSize: axisLabelFont }}
            fill="#111827"
          />
        )}
      </XAxis>

      <YAxis
        domain={[min, max]}
        width={yWidth}                 // skinny on mobile
        tickMargin={compact ? 2 : 6}
        tick={yTickProp}
        ticks={yTicks}
        tickFormatter={yTickFormatter}
        axisLine={!compact}
        tickLine={!compact}
      >
        {showAxisLabels && yLabel && (
          <Label
            value={yLabel}
            angle={-90}
            position="left"
            offset={Y_LABEL_OFFSET}
            style={{ textAnchor: "middle", fontSize: axisLabelFont }}
            fill="#111827"
          />
        )}
      </YAxis>

      <Tooltip
        formatter={tooltipFormatter}
        labelFormatter={tooltipLabelFormatter}
        wrapperStyle={{ fontSize: Math.max(tickFont, 10) }}
      />
    </>
  );

  return (
    <ResponsiveContainer width="100%" height="100%">
      {chart === "bar" ? (
        <BarChart data={data} margin={margins}>
          <Axes />
          <Bar dataKey={yKey} fill={color} radius={[6, 6, 0, 0]} />
        </BarChart>
      ) : (
        <LineChart data={data} margin={margins}>
          <Axes />
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={color}
            strokeWidth={2}
            dot={lineDot}
            activeDot={lineActiveDot}
          />
        </LineChart>
      )}
    </ResponsiveContainer>
  );
};

export default ChartBase;


// import React from "react";
// import {
//   ResponsiveContainer,
//   LineChart, Line,
//   BarChart, Bar,
//   XAxis, YAxis, CartesianGrid, Tooltip, Label
// } from "recharts";

// const DEFAULT_MARGIN = { top: 12, right: 16, bottom: 14, left: 24 };
// const Y_LABEL_OFFSET = 18;

// const paddedDomain = (data, key, padPct = 0.08) => {
//   if (!data || !data.length) return ["auto", "auto"];
//   let min = Infinity, max = -Infinity;
//   for (const d of data) {
//     const v = Number(d?.[key]);
//     if (Number.isFinite(v)) { if (v < min) min = v; if (v > max) max = v; }
//   }
//   if (!Number.isFinite(min) || !Number.isFinite(max)) return ["auto", "auto"];
//   const range = Math.max(1e-6, max - min);
//   const pad = range * padPct;
//   return [min - pad, max + pad];
// };

// const estimateYWidthFromDomain = (min, max, decimals = 2) => {
//   if (!Number.isFinite(min) || !Number.isFinite(max)) return 50;
//   const s1 = min.toFixed(decimals);
//   const s2 = max.toFixed(decimals);
//   const longest = Math.max(s1.length, s2.length);
//   return Math.min(96, Math.max(44, longest * 8 + 14));
// };

// const ChartBase = ({
//   chart = "line",
//   data = [],
//   xKey = "t",
//   yKey,
//   xLabel = "Time",
//   yLabel,
//   color = "#4f46e5",
//   decimals = 2,
//   yPadPct = 0.08,
//   yTicks,
//   yTickFormatter,
//   tooltipFormatter,

//   /* numeric x-axis controls */
//   xType = "category",
//   xDomain,
//   xTicks,
//   xTickFormatter,
//   tooltipLabelFormatter,

//   /* line dot controls */
//   lineDot = false,
//   lineActiveDot = { r: 4 },

//   /* NEW: mobile-aware knobs */
//   margins = DEFAULT_MARGIN,   
//   tickFont = 12,          
//   axisLabelFont = 12,     
//   showAxisLabels = true, 
//   yAxisMinWidth = 44, 
//   compact = false,
// }) => {
//   const [min, max] = paddedDomain(data, yKey, yPadPct);
//   const yWidth = Math.max(yAxisMinWidth, estimateYWidthFromDomain(min, max, decimals)); // ← CHANGED

//   const tickStyle = { fill: "#374151", fontSize: tickFont }; // ← CHANGED
//   const xTickProp = compact ? false : tickStyle;
//   const yTickProp = compact ? { ...tickStyle } : tickStyle;

//   const Axes = () => (
//     <>
//       <CartesianGrid strokeDasharray="3 3" />
//       <XAxis
//         dataKey={xKey}
//         type={xType}
//         domain={xDomain}
//         ticks={xTicks}
//         tickFormatter={xTickFormatter}
//         tick={xTickProp}
//         tickMargin={compact ? 2 : 4}
//         axisLine={!compact}
//         tickLine={!compact}
//       >
//         {showAxisLabels && xLabel && (
//           <Label
//             value={xLabel}
//             position="insideBottom"
//             dy={12}
//             style={{ fontSize: axisLabelFont }}
//             fill="#111827"
//           />
//         )}
//       </XAxis>

//       <YAxis
//         domain={[min, max]}
//         width={yWidth}
//         tickMargin={compact ? 2 : 6}
//         tick={yTickProp}
//         ticks={yTicks}
//         tickFormatter={yTickFormatter}
//         axisLine={!compact}
//         tickLine={!compact}
//       >
//         {showAxisLabels && yLabel && (
//           <Label
//             value={yLabel}
//             angle={-90}
//             position="left"
//             offset={Y_LABEL_OFFSET}
//             style={{ textAnchor: "middle", fontSize: axisLabelFont }}
//             fill="#111827"
//           />
//         )}
//       </YAxis>

//       <Tooltip
//         formatter={tooltipFormatter}
//         labelFormatter={tooltipLabelFormatter}
//         wrapperStyle={{ fontSize: Math.max(tickFont, 10) }}
//       />
//     </>
//   );

//   return (
//     <ResponsiveContainer width="100%" height="100%">
//       {chart === "bar" ? (
//         <BarChart data={data} margin={margins}>
//           <Axes />
//           <Bar dataKey={yKey} fill={color} radius={[6, 6, 0, 0]} />
//         </BarChart>
//       ) : (
//         <LineChart data={data} margin={margins}>
//           <Axes />
//           <Line
//             type="monotone"
//             dataKey={yKey}
//             stroke={color}
//             strokeWidth={2}
//             dot={lineDot}
//             activeDot={lineActiveDot}
//           />
//         </LineChart>
//       )}
//     </ResponsiveContainer>
//   );
// };

// export default ChartBase;
