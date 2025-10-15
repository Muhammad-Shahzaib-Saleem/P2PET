import React, { useEffect, useState } from "react";
import { fetchEnergyDashboard } from "../../../api/energy";
import CustomerCard from "../CustomerCard/CustomerCard";
import CostPredictedCard from "../CostPredictedCard/CostPredictedCard";
import ChartsTabs from "../ChartsTabs/ChartsTabs";
import "./EnergyDashboardView.css";

// Set your real tariffs or read them from the payload (see below)
const DEFAULT_IMPORT_RATE = 60; // Rs per kWh for grid import
const DEFAULT_EXPORT_RATE = 18; // Rs per kWh credit for export

const EnergyDashboardView = () => {
  const [loading, setLoading] = useState(true);
  const [payload, setPayload] = useState({ customer: null, costs: null, charts: null });
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetchEnergyDashboard();
        if (!mounted) return;
        setPayload(res);
        setLoading(false);
      } catch (e) {
        setError("Failed to load dashboard data");
        setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  if (loading) return <div className="edv-page">Loading dashboard…</div>;
  if (error) return <div className="edv-page">{error}</div>;

  // Prefer server-provided rates; fallback to defaults
  const importRatePKR =
    payload?.pricing?.importPerKwh ??
    payload?.rates?.importPerKwh ??
    DEFAULT_IMPORT_RATE;

  const exportRatePKR =
    payload?.pricing?.exportPerKwh ??
    payload?.rates?.exportPerKwh ??
    DEFAULT_EXPORT_RATE;

  return (
    <div className="edv-page">
      <div className="edv-top-grid">
        <CustomerCard data={payload.customer} />
        <CostPredictedCard
          costs={payload.costs}
          importRatePKR={importRatePKR}
          exportRatePKR={exportRatePKR}
        />
      </div>
      <ChartsTabs charts={payload.charts} />
    </div>
  );
};

export default EnergyDashboardView;
