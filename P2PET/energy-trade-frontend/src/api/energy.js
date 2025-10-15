// src/api/energy.js
// Mock API for the Energy Dashboard. Swap with real fetch/axios later.
import sample from "../assets/energySample.json";

/* ------------------------------ helpers ------------------------------ */
const sleep = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const clone = (v) => JSON.parse(JSON.stringify(v));

/* ------------------------------ core API ----------------------------- */
export const fetchCustomer = async () => {
  await sleep();
  return clone(sample.customer);
};

export const fetchCosts = async () => {
  await sleep();
  return clone(sample.costs);
};

export const fetchCharts = async () => {
  await sleep();
  return clone(sample.charts);
};

/**
 * Convenience call to fetch everything needed by the dashboard in one shot.
 */
export const fetchEnergyDashboard = async () => {
  await sleep();
  return clone({
    customer: sample.customer,
    costs: sample.costs,
    charts: sample.charts,
  });
};

/* ----------------------- energy-specific helpers --------------------- */

/**
 * List of day keys available in weekly energy data (e.g., ["Mon","Tue",...]).
 */
export const listEnergyDays = async () => {
  await sleep(30);
  return clone((sample?.charts?.energy || []).map((d) => d.t));
};

/**
 * Fetch hourly consumption for a given day.
 * - If `sample.energyHourly[dayKey]` exists, use it.
 * - Otherwise, synthesize 24 hourly buckets from that day's total kWh.
 *
 * @param {string} dayKey - e.g., "Mon", "Tue", ...
 * @returns {Promise<Array<{h: string, kwh: number}>>}
 */
export const fetchEnergyHoursForDay = async (dayKey) => {
  await sleep();

  if (!dayKey) return [];

  // 1) Prefer real hourly data from the JSON, if present
  const hourlyFromJson = sample?.energyHourly?.[dayKey];
  if (hourlyFromJson && Array.isArray(hourlyFromJson)) {
    return clone(hourlyFromJson);
  }

  // 2) Fallback: synthesize from weekly total for that day
  const dayObj = (sample?.charts?.energy || []).find((d) => d.t === dayKey);
  const total = typeof dayObj?.kwh === "number" ? dayObj.kwh : 12;

  // Build a simple diurnal curve so the shape looks realistic
  const base = total / 24;
  const hours = Array.from({ length: 24 }, (_, h) => {
    // Label like "00:00", "01:00", ...
    const label = `${String(h).padStart(2, "0")}:00`;

    // Day shape: quiet overnight, ramp up in morning/evening
    // Combines a sine wave + small bias to avoid zeros
    const wave = 1 + 0.35 * Math.sin((2 * Math.PI * (h - 6)) / 24); // peak ~noon/evening
    const jitter = 1 + (Math.random() - 0.5) * 0.08; // ±4% random
    const kwh = +(base * wave * jitter).toFixed(2);

    return { h: label, kwh };
  });

  // Normalize to roughly match the daily total (optional)
  const sum = hours.reduce((s, x) => s + x.kwh, 0) || 1;
  const scale = total / sum;
  const normalized = hours.map((x) => ({ h: x.h, kwh: +(x.kwh * scale).toFixed(2) }));

  return normalized;
};



// // src/api/energy.js
// // Swap this with real fetch/axios when backend is ready.
// import sample from "../assets/energySample.json";

// // Simulate async endpoints
// export const fetchCustomer = async () => {
//   return Promise.resolve(sample.customer);
// };

// export const fetchCosts = async () => {
//   return Promise.resolve(sample.costs);
// };

// export const fetchCharts = async () => {
//   return Promise.resolve(sample.charts);
// };

// // (Convenience) single call
// export const fetchEnergyDashboard = async () => {
//   return Promise.resolve({
//     customer: sample.customer,
//     costs: sample.costs,
//     charts: sample.charts,
//   });
// };
