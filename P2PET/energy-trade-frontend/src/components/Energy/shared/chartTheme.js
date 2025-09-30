// shared chart constants / formatters (no repetition across components)

export const ENERGY_COLORS = {
  import: "#16a34a", // emerald-600
  export: "#ef4444", // red-500
};

export const formatKwh = (v, digits = 2) =>
  `${Number(v ?? 0).toFixed(digits)} kWh`;

export const formatPKR = (v) =>
  `₨ ${Number(v ?? 0).toLocaleString("en-PK", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
