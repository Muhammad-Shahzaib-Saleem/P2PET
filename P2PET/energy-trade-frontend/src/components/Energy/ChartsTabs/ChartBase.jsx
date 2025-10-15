import React from "react";
import {
  ResponsiveContainer,
  LineChart, Line,
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Label
} from "recharts";

const COMMON_MARGIN = { top: 10, right: 16, bottom: 36, left: 30 };
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

  /* NEW: numeric x-axis controls */
  xType = "category",     // "category" or "number"
  xDomain,
  xTicks,
  xTickFormatter,
  tooltipLabelFormatter,

  /* NEW: line dot controls */
  lineDot = false,
  lineActiveDot = { r: 4 },
}) => {
  const [min, max] = paddedDomain(data, yKey, yPadPct);
  const yWidth = estimateYWidthFromDomain(min, max, decimals);

  const commonAxes = (
    <>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis
        dataKey={xKey}
        type={xType}
        domain={xDomain}
        ticks={xTicks}
        tickFormatter={xTickFormatter}
      >
        <Label value={xLabel} position="insideBottom" dy={14} fill="#111827" />
      </XAxis>
      <YAxis
        domain={[min, max]}
        width={yWidth}
        tickMargin={6}
        tick={{ fill: "#374151" }}
        ticks={yTicks}
        tickFormatter={yTickFormatter}
      >
        <Label
          value={yLabel}
          angle={-90}
          position="left"
          offset={Y_LABEL_OFFSET}
          style={{ textAnchor: "middle" }}
          fill="#111827"
        />
      </YAxis>
      <Tooltip formatter={tooltipFormatter} labelFormatter={tooltipLabelFormatter} />
    </>
  );

  return (
    <ResponsiveContainer width="100%" height="100%">
      {chart === "bar" ? (
        <BarChart data={data} margin={COMMON_MARGIN}>
          {commonAxes}
          <Bar dataKey={yKey} fill={color} radius={[6, 6, 0, 0]} />
        </BarChart>
      ) : (
        <LineChart data={data} margin={COMMON_MARGIN}>
          {commonAxes}
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
