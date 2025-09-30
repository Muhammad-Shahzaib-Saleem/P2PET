import React from "react";
import {
  ResponsiveContainer, PieChart, Pie, Cell, Legend, Tooltip
} from "recharts";
import { ENERGY_COLORS, formatKwh, formatPKR } from "../shared/chartTheme";
import "./CostPredictedCard.css";

/** Force all inputs to 2 slices: Import (green), Export (red) */
const normalizeToImportExport = (items = []) =>
  items.map((d, i) => {
    const raw = (d.type || d.name || "").toString().toLowerCase();

    let kind;
    if (raw.includes("import")) kind = "import";
    else if (raw.includes("export")) kind = "export";
    else if (raw.includes("electricity")) kind = "import"; // Electricity -> Import
    else if (raw.includes("gas")) kind = "export";         // Gas -> Export
    else kind = i === 0 ? "import" : "export";             // fallback by position

    const kwh = Number(d.kwh ?? d.value ?? 0);
    const pkr = Number(d.pkr ?? d.cost ?? NaN); // may be missing

    return {
      kind,
      name: kind === "import" ? "Import kWh" : "Export kWh",
      value: kwh, // used for slice size (kWh)
      pkr,       // may be NaN (i.e., not provided by backend)
      color: kind === "import" ? ENERGY_COLORS.import : ENERGY_COLORS.export,
    };
  });

/**
 * Props:
 *  - costs: raw array from API
 *  - importRatePKR: Rs/kWh to charge for import (default 60)
 *  - exportRatePKR: Rs/kWh credit for export (default 18)
 */
const CostPredictedCard = ({ costs, importRatePKR = 60, exportRatePKR = 18 }) => {
  if (!costs || !costs.length) return null;

  const slices = normalizeToImportExport(costs).map((s) => {
    // If backend already sent pkr, keep it; else compute:
    if (Number.isFinite(s.pkr) && s.pkr !== 0) return s;

    const computed =
      s.kind === "import"
        ? s.value * importRatePKR      // cost (positive)
        : -s.value * exportRatePKR;    // credit (negative)

    return { ...s, pkr: computed };
  });

  const totalPKR = slices.reduce((sum, s) => sum + (Number.isFinite(s.pkr) ? s.pkr : 0), 0);

  return (
    <div className="cpc-card">
      <div className="cpc-header">
        <h3>Cost Predicted</h3>
        <span className="cpc-pill">Next 24h</span>
      </div>

      <div className="cpc-body">
        <div className="cpc-pie-wrap">
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={slices}
                dataKey="value"      // kWh determines slice size
                nameKey="name"       // legend/tooltip label
                innerRadius={40}
                outerRadius={62}
                paddingAngle={2}
                isAnimationActive={false}
              >
                {slices.map((s, idx) => (
                  <Cell key={idx} fill={s.color} />
                ))}
              </Pie>

              <Legend
                layout="vertical"
                verticalAlign="middle"
                align="right"
                iconType="circle"
              />

              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const { name, value, pkr, color } = payload[0].payload;
                  return (
                    <div className="cpc-tooltip">
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ width: 10, height: 10, borderRadius: 999, background: color }} />
                        <strong>{name}</strong>
                      </div>
                      <div>{formatKwh(value)}</div>
                      {/* export credit will naturally show with a minus sign */}
                      {Number.isFinite(pkr) && <div>{formatPKR(pkr)}</div>}
                    </div>
                  );
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          <div className="cpc-total">
            <div className="cpc-total-label">Total</div>
            <div className="cpc-total-value">{formatPKR(totalPKR)}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostPredictedCard;
