import React, { useState } from "react";
import ChartBase from "./ChartBase";
import EnergyDualBar from "./EnergyDualBar";
import EnergyHourlyModal from "./EnergyHourlyModal";
import "./ChartsTabs.css";

/* ------- frequency ticks helper ------- */
const makeFreqTicksFromData = (data, key = "f", step = 0.2, padPct = 0.06) => {
  if (!data || !data.length) return undefined;
  let min = Infinity, max = -Infinity;
  for (const d of data) {
    const v = Number(d?.[key]);
    if (Number.isFinite(v)) { if (v < min) min = v; if (v > max) max = v; }
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) return undefined;
  const range = Math.max(1e-6, max - min);
  const pad = range * padPct;
  min -= pad; max += pad;
  const out = [];
  const start = Math.ceil(min / step) * step;
  for (let v = start; v <= max + 1e-9; v += step) out.push(+v.toFixed(1));
  return out;
};

/* ---------- Energy helpers ---------- */
const DAY = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

const normalizeEnergyRow = (row = {}) => {
  const key = (row.t || row.day || row.d || "").toString().slice(0,3);
  const importKwh = Number(row.importKwh ?? row.kwh ?? 0);
  const exportKwh = Number(row.exportKwh ?? 0);
  return { key, importKwh, exportKwh };
};

const buildLastWeekSeries = (raw = []) => {
  const m = new Map();
  raw.forEach(r => {
    const n = normalizeEnergyRow(r);
    if (n.key) m.set(n.key, { importKwh: n.importKwh, exportKwh: n.exportKwh });
  });
  const today = new Date();
  const out = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = DAY[d.getDay()];
    const label = i === 0 ? "Today" : key;
    const row = m.get(key) || { importKwh: 0, exportKwh: 0 };
    out.push({ t: label, importKwh: row.importKwh, exportKwh: row.exportKwh });
  }
  return out;
};

/* ---- Hourly detail helpers ---- */
const pad2 = (n) => (n < 10 ? "0" + n : "" + n);

const normalizeHourLabel = (h) => {
  if (typeof h === "number") return `${pad2(h)}:00`;
  const s = String(h ?? "").trim();
  const m = s.match(/^(\d{1,2})(?::?(\d{2}))?$/);
  if (m) return `${pad2(Number(m[1]))}:00`;
  return s || "00:00";
};

const normalizeEnergyHourlyMap = (raw) => {
  const map = {};
  if (!raw) return map;
  Object.keys(raw).forEach(dayKey => {
    const short = dayKey.slice(0,3);
    const arr = raw[dayKey] || [];
    map[short] = arr.map(r => ({
      t: normalizeHourLabel(r.t ?? r.h ?? r.hour),
      importKwh: Number(r.importKwh ?? r.kwh ?? 0),
      exportKwh: Number(r.exportKwh ?? 0),
    }));
  });
  return map;
};

const buildHourlyForDay = (shortKey, energyWeekRow, energyHourlyRaw) => {
  const hourlyMap = normalizeEnergyHourlyMap(energyHourlyRaw);
  let rows = hourlyMap[shortKey];
  if (!rows || !rows.length) {
    // Demo fallback: evenly split daily totals into 24 hours
    const slots = 24;
    const imp = Number(energyWeekRow?.importKwh ?? 0) / slots;
    const exp = Number(energyWeekRow?.exportKwh ?? 0) / slots;
    rows = Array.from({ length: slots }, (_, i) => ({
      t: `${pad2(i)}:00`,
      importKwh: +imp.toFixed(2),
      exportKwh: +exp.toFixed(2),
    }));
  }
  return rows.sort((a, b) => a.t.localeCompare(b.t));
};

/* ---------------- strict last-hour from NOW ---------------- */
const HOUR_MS  = 60 * 60 * 1000;
const TICK_MIN = 4;

const fmtHmma = (ms) => {
  const d = new Date(ms);
  let h = d.getHours(), m = d.getMinutes();
  const ap = h >= 12 ? "pm" : "am";
  h = h % 12; if (h === 0) h = 12;
  return `${h}:${pad2(m)} ${ap}`;
};

const parseTimeMs = (t, now = new Date()) => {
  if (t == null) return NaN;
  if (t instanceof Date) return t.getTime();
  if (typeof t === "number") return Number.isFinite(t) ? t : NaN;

  const s = String(t).trim();
  const iso = Date.parse(s);
  if (!Number.isNaN(iso)) return iso;

  const m = s.match(/^(\d{1,2}):(\d{2})$/);
  if (m) {
    const hh = Number(m[1]), mm = Number(m[2]);
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hh, mm, 0, 0);
    const nowMin = now.getHours() * 60 + now.getMinutes();
    const tMin   = hh * 60 + mm;
    if (tMin > nowMin) d.setDate(d.getDate() - 1); // midnight rollover
    return d.getTime();
  }
  return NaN;
};

const makeTimeTicks = (startMs, endMs, everyMin = TICK_MIN) => {
  const step = everyMin * 60 * 1000;
  const first = Math.ceil(startMs / step) * step;
  const ticks = [];
  for (let t = first; t <= endMs; t += step) ticks.push(t);
  return ticks;
};

const buildWindowFromNow = (rows = [], tKey = "t", nowMs = Date.now()) => {
  const start = nowMs - HOUR_MS;
  const parsed = rows
    .map(d => ({ ...d, ts: parseTimeMs(d?.[tKey], new Date(nowMs)) }))
    .filter(d => Number.isFinite(d.ts))
    .sort((a, b) => a.ts - b.ts);

  const within = parsed.filter(d => d.ts >= start && d.ts <= nowMs);
  return {
    data: within,
    domain: [start, nowMs],
    ticks: makeTimeTicks(start, nowMs),
  };
};

/* ---------------- Component ---------------- */
const ChartsTabs = ({ charts }) => {
  const nowMs = Date.now();

  // strict last hour for V/F/A
  const vWin = buildWindowFromNow(charts?.voltage   || [], "t", nowMs);
  const fWin = buildWindowFromNow(charts?.frequency || [], "t", nowMs);
  const aWin = buildWindowFromNow(charts?.amperage  || [], "t", nowMs);

  // Energy weekly
  const energyWeek = buildLastWeekSeries(charts?.energy || []);

  // Modal state (hourly drilldown)
  const [hourlyOpen, setHourlyOpen] = useState(false);
  const [hourlyLabel, setHourlyLabel] = useState("");
  const [hourlyRows, setHourlyRows] = useState([]);

  const handleSelectDay = (row) => {
    const label = row?.t || "";
    const short = label === "Today" ? DAY[new Date().getDay()] : label.slice(0,3);
    const weekRow = energyWeek.find(d => d.t === label);
    const rows = buildHourlyForDay(short, weekRow, charts?.energyHourly);
    setHourlyLabel(label);
    setHourlyRows(rows);
    setHourlyOpen(true);
  };

  const tabs = [
    {
      key: "voltage",
      label: "Voltage",
      render: () => (
        <ChartBase
          chart="line"
          data={vWin.data}
          xKey="ts"
          xType="number"
          xDomain={vWin.domain}
          xTicks={vWin.ticks}
          xTickFormatter={fmtHmma}
          tooltipLabelFormatter={fmtHmma}
          yKey="v"
          xLabel="Time"
          yLabel="Voltage (V)"
          color="#4f46e5"
          decimals={2}
          lineDot={true}
          lineActiveDot={{ r: 5 }}
        />
      ),
    },
    {
      key: "energy",
      label: "Energy Consumption",
      render: () => (
        <>
          <EnergyDualBar
            data={energyWeek}
            xLabel="Day"
            onSelectItem={handleSelectDay}     // open modal on click
          />
          <EnergyHourlyModal
            open={hourlyOpen}
            dayLabel={hourlyLabel}
            rows={hourlyRows}
            onClose={() => setHourlyOpen(false)}
          />
        </>
      ),
    },
    {
      key: "frequency",
      label: "Frequency",
      render: () => (
        <ChartBase
          chart="line"
          data={fWin.data}
          xKey="ts"
          xType="number"
          xDomain={fWin.domain}
          xTicks={fWin.ticks}
          xTickFormatter={fmtHmma}
          tooltipLabelFormatter={fmtHmma}
          yKey="f"
          xLabel="Time"
          yLabel="Frequency (Hz)"
          color="#0ea5e9"
          decimals={1}
          yPadPct={0.06}
          yTicks={makeFreqTicksFromData(fWin.data)}
          yTickFormatter={(v) => v.toFixed(1)}
          tooltipFormatter={(v) => [Number(v).toFixed(1), "f"]}
          lineDot={true}
          lineActiveDot={{ r: 5 }}
        />
      ),
    },
    {
      key: "amperage",
      label: "Amperage",
      render: () => (
        <ChartBase
          chart="line"
          data={aWin.data}
          xKey="ts"
          xType="number"
          xDomain={aWin.domain}
          xTicks={aWin.ticks}
          xTickFormatter={fmtHmma}
          tooltipLabelFormatter={fmtHmma}
          yKey="a"
          xLabel="Time"
          yLabel="Current (A)"
          color="#f59e0b"
          decimals={1}
          lineDot={true}
          lineActiveDot={{ r: 5 }}
        />
      ),
    },
  ];

  const [active, setActive] = useState(tabs[0].key);

  return (
    <div className="ct-card">
      <div className="ct-header">
        <h3>Charts</h3>
        <div className="ct-tabs">
          {tabs.map((t) => (
            <button
              key={t.key}
              className={`ct-tab ${active === t.key ? "active" : ""}`}
              onClick={() => setActive(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="ct-body">
        <div className="ct-chart-area">
          {tabs.find((t) => t.key === active)?.render()}
        </div>
      </div>
    </div>
  );
};

export default ChartsTabs;


// import React, { useState } from "react";
// import ChartBase from "./ChartBase";
// import EnergyDualBar from "./EnergyDualBar";
// import "./ChartsTabs.css";

// /* ------- frequency ticks helper (unchanged) ------- */
// const makeFreqTicksFromData = (data, key = "f", step = 0.2, padPct = 0.06) => {
//   if (!data || !data.length) return undefined;
//   let min = Infinity, max = -Infinity;
//   for (const d of data) {
//     const v = Number(d?.[key]);
//     if (Number.isFinite(v)) { if (v < min) min = v; if (v > max) max = v; }
//   }
//   if (!Number.isFinite(min) || !Number.isFinite(max)) return undefined;
//   const range = Math.max(1e-6, max - min);
//   const pad = range * padPct;
//   min -= pad; max += pad;
//   const out = [];
//   const start = Math.ceil(min / step) * step;
//   for (let v = start; v <= max + 1e-9; v += step) out.push(+v.toFixed(1));
//   return out;
// };

// /* ---------- Energy helpers (unchanged) ---------- */
// const DAY = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
// const normalizeEnergyRow = (row = {}) => {
//   const key = (row.t || row.day || row.d || "").toString().slice(0,3);
//   const importKwh = Number(row.importKwh ?? row.kwh ?? 0);
//   const exportKwh = Number(row.exportKwh ?? 0);
//   return { key, importKwh, exportKwh };
// };
// const buildLastWeekSeries = (raw = []) => {
//   const m = new Map();
//   raw.forEach(r => {
//     const n = normalizeEnergyRow(r);
//     if (n.key) m.set(n.key, { importKwh: n.importKwh, exportKwh: n.exportKwh });
//   });
//   const today = new Date();
//   const out = [];
//   for (let i = 6; i >= 0; i--) {
//     const d = new Date(today);
//     d.setDate(today.getDate() - i);
//     const key = DAY[d.getDay()];
//     const label = i === 0 ? "Today" : key;
//     const row = m.get(key) || { importKwh: 0, exportKwh: 0 };
//     out.push({ t: label, importKwh: row.importKwh, exportKwh: row.exportKwh });
//   }
//   return out;
// };

// /* ---------------- strict last-hour from NOW ---------------- */
// const HOUR_MS  = 60 * 60 * 1000;
// const TICK_MIN = 4; // change to 3 for 3-minute ticks

// const pad2 = (n) => (n < 10 ? "0" + n : "" + n);
// const fmtHmma = (ms) => {
//   const d = new Date(ms);
//   let h = d.getHours(), m = d.getMinutes();
//   const ap = h >= 12 ? "pm" : "am";
//   h = h % 12; if (h === 0) h = 12;
//   return `${h}:${pad2(m)} ${ap}`;
// };

// /* parse ISO or "HH:mm". If "HH:mm" is ahead of current clock, treat as yesterday. */
// const parseTimeMs = (t, now = new Date()) => {
//   if (t == null) return NaN;
//   if (t instanceof Date) return t.getTime();
//   if (typeof t === "number") return Number.isFinite(t) ? t : NaN;

//   const s = String(t).trim();
//   const iso = Date.parse(s);
//   if (!Number.isNaN(iso)) return iso;

//   const m = s.match(/^(\d{1,2}):(\d{2})$/);
//   if (m) {
//     const hh = Number(m[1]), mm = Number(m[2]);
//     const d = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hh, mm, 0, 0);
//     const nowMin = now.getHours() * 60 + now.getMinutes();
//     const tMin   = hh * 60 + mm;
//     if (tMin > nowMin) d.setDate(d.getDate() - 1); // midnight rollover
//     return d.getTime();
//   }
//   return NaN;
// };

// /* ticks inside [start,end] every X minutes */
// const makeTimeTicks = (startMs, endMs, everyMin = TICK_MIN) => {
//   const step = everyMin * 60 * 1000;
//   const first = Math.ceil(startMs / step) * step;
//   const ticks = [];
//   for (let t = first; t <= endMs; t += step) ticks.push(t);
//   return ticks;
// };

// /** Build window = [now-1h, now]; filter data into it; always use this domain
//  *   so the x-axis shows the previous hour correctly. */
// const buildWindowFromNow = (rows = [], tKey = "t", nowMs = Date.now()) => {
//   const start = nowMs - HOUR_MS;
//   const parsed = rows
//     .map(d => ({ ...d, ts: parseTimeMs(d?.[tKey], new Date(nowMs)) }))
//     .filter(d => Number.isFinite(d.ts))
//     .sort((a, b) => a.ts - b.ts);

//   const within = parsed.filter(d => d.ts >= start && d.ts <= nowMs);
//   return {
//     data: within,                               // may be empty if no points in last hour
//     domain: [start, nowMs],
//     ticks: makeTimeTicks(start, nowMs),
//   };
// };

// const ChartsTabs = ({ charts }) => {
//   const nowMs = Date.now();

//   // strict last hour for V/F/A
//   const vWin = buildWindowFromNow(charts?.voltage   || [], "t", nowMs);
//   const fWin = buildWindowFromNow(charts?.frequency || [], "t", nowMs);
//   const aWin = buildWindowFromNow(charts?.amperage  || [], "t", nowMs);

//   // Energy dual bars
//   const energyWeek = buildLastWeekSeries(charts?.energy || []);

//   const tabs = [
//     {
//       key: "voltage",
//       label: "Voltage",
//       render: () => (
//         <ChartBase
//           chart="line"
//           data={vWin.data}
//           xKey="ts"
//           xType="number"
//           xDomain={vWin.domain}
//           xTicks={vWin.ticks}
//           xTickFormatter={fmtHmma}
//           tooltipLabelFormatter={fmtHmma}
//           yKey="v"
//           xLabel="Time"
//           yLabel="Voltage (V)"
//           color="#4f46e5"
//           decimals={2}
//           lineDot={true}                 // <-- dots enabled for hover on each point
//           lineActiveDot={{ r: 5 }}
//         />
//       ),
//     },
//     {
//       key: "energy",
//       label: "Energy Consumption",
//       render: () => <EnergyDualBar data={energyWeek} />,
//     },
//     {
//       key: "frequency",
//       label: "Frequency",
//       render: () => (
//         <ChartBase
//           chart="line"
//           data={fWin.data}
//           xKey="ts"
//           xType="number"
//           xDomain={fWin.domain}
//           xTicks={fWin.ticks}
//           xTickFormatter={fmtHmma}
//           tooltipLabelFormatter={fmtHmma}
//           yKey="f"
//           xLabel="Time"
//           yLabel="Frequency (Hz)"
//           color="#0ea5e9"
//           decimals={1}
//           yPadPct={0.06}
//           yTicks={makeFreqTicksFromData(fWin.data)}
//           yTickFormatter={(v) => v.toFixed(1)}
//           tooltipFormatter={(v) => [Number(v).toFixed(1), "f"]}
//           lineDot={true}
//           lineActiveDot={{ r: 5 }}
//         />
//       ),
//     },
//     {
//       key: "amperage",
//       label: "Amperage",
//       render: () => (
//         <ChartBase
//           chart="line"
//           data={aWin.data}
//           xKey="ts"
//           xType="number"
//           xDomain={aWin.domain}
//           xTicks={aWin.ticks}
//           xTickFormatter={fmtHmma}
//           tooltipLabelFormatter={fmtHmma}
//           yKey="a"
//           xLabel="Time"
//           yLabel="Current (A)"
//           color="#f59e0b"
//           decimals={1}
//           lineDot={true}
//           lineActiveDot={{ r: 5 }}
//         />
//       ),
//     },
//   ];

//   const [active, setActive] = useState(tabs[0].key);

//   return (
//     <div className="ct-card">
//       <div className="ct-header">
//         <h3>Charts</h3>
//         <div className="ct-tabs">
//           {tabs.map((t) => (
//             <button
//               key={t.key}
//               className={`ct-tab ${active === t.key ? "active" : ""}`}
//               onClick={() => setActive(t.key)}
//             >
//               {t.label}
//             </button>
//           ))}
//         </div>
//       </div>

//       <div className="ct-body">
//         <div className="ct-chart-area">
//           {tabs.find((t) => t.key === active)?.render()}
//         </div>
//       </div>
//     </div>
//   );
// };

// export default ChartsTabs;
