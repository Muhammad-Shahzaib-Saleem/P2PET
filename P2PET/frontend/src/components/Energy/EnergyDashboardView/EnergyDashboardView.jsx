// src/components/EnergyDashboard/EnergyDashboardView.jsx
import React, { useEffect, useState } from "react";
import Button from "../../Button/Button";
import SearchBar from "../../SearchBar/SearchBar";
import ViewToggle from "../../ViewToggle/ViewToggle";
import "./EnergyDashboardView.css";

// 👇 Your Pi endpoints
const PIS = [
  { id: 1, name: "Pi 1", ip: "http://100.76.91.82:8001" },
  { id: 2, name: "Pi 2", ip: "http://100.93.80.36:8002" },
  { id: 3, name: "Pi 3", ip: "http://100.71.238.87:8003" },
  { id: 4, name: "Pi 4", ip: "http://100.80.205.106:8004" },
  { id: 4, name: "Pi 11", ip: "http://100.120.139.128:8005" },
  { id: 5, name: "Pi 13", ip: "http://100.80.11.48:8006" },
  { id: 6, name: "Pi 15", ip: "http://100.120.124.29:8007" },
];

const EnergyDashboardView = () => {
  const [pisData, setPisData] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [viewMode, setViewMode] = useState("cards");
  const [searchActive, setSearchActive] = useState(false);

  // ✅ safe fetch helper
  const safeFetch = async (url, timeout = 4000) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
      const res = await fetch(url, { signal: controller.signal });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      return await res.json();
    } finally {
      clearTimeout(id);
    }
  };

  // 🔁 Fetch all Pis (FIXED LOGIC)
  const fetchAll = async () => {
    const results = await Promise.allSettled(
      PIS.map(async (pi) => {
        let meter = null;
        let transfer = null;

        // ✅ Meter is REQUIRED (defines ONLINE/OFFLINE)
        try {
          meter = await safeFetch(`${pi.ip}/meter/all`);
        } catch (err) {
          console.warn(`Meter failed: ${pi.name}`, err.message);

          return {
            ...pi,
            status: "offline",
            error: "Meter unreachable",
          };
        }

        // ✅ Transfer is OPTIONAL (never breaks UI)
        try {
          transfer = await safeFetch(`${pi.ip}/transfer/status`);
        } catch (err) {
          console.warn(`Transfer failed: ${pi.name}`, err.message);

          transfer = {
            active: false,
            relay_on: false,
            threshold_kwh: 0,
          };
        }

        return {
          ...pi,
          meter,
          transfer,
          status: "online",
        };
      })
    );

    const data = results.map((r) =>
      r.status === "fulfilled"
        ? r.value
        : { status: "offline", error: "Unknown error" }
    );

    setPisData(data);
    setFiltered(data);
  };

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 5000);
    return () => clearInterval(id);
  }, []);

  // 🔍 Search
  const handleSearch = (query) => {
    if (!query.trim()) {
      setFiltered(pisData);
    } else {
      const q = query.toLowerCase();
      setFiltered(
        pisData.filter((pi) => pi.name.toLowerCase().includes(q))
      );
    }
  };

  const toggleView = () =>
    setViewMode((v) => (v === "cards" ? "table" : "cards"));

  return (
    <div className={`dashboard-container ${searchActive ? "search-active" : ""}`}>
      <div className="dashboard-header">
        <h1 className="dashboard-title">Energy Monitoring Dashboard</h1>

        <div className="header-controls">
          <SearchBar onSearch={handleSearch} onActiveChange={setSearchActive} />

          <div className="hide-on-search">
            <ViewToggle viewMode={viewMode} onToggle={toggleView} />
          </div>

          <div className="hide-on-search">
            <Button text="Refresh" onClick={fetchAll} />
          </div>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">No devices found</div>
      ) : viewMode === "cards" ? (
        <div className="meter-list">
          {filtered.map((pi) => (
            <div className="meter-card" key={pi.id}>
              <div className="meter-details">
                <h3 className="meter-name">{pi.name}</h3>

                {/* STATUS */}
                <div className="meter-row">
                  <span>Status</span>
                  <span className={`status ${pi.status}`}>
                    {pi.status}
                  </span>
                </div>

                {/* ERROR */}
                {pi.status === "offline" && (
                  <div className="error-text">
                    {pi.error || "Device unreachable"}
                  </div>
                )}

                {/* METER DATA */}
                {pi.status === "online" && (
                  <>
                    <div className="meter-row">
                      <span>Voltage</span>
                      <span>{pi.meter?.voltage_v?.toFixed(1) ?? "-"} V</span>
                    </div>

                    <div className="meter-row">
                      <span>Current</span>
                      <span>{pi.meter?.current_a?.toFixed(2) ?? "-"} A</span>
                    </div>

                    <div className="meter-row">
                      <span>Power</span>
                      <span>{pi.meter?.power_w?.toFixed(0) ?? "-"} W</span>
                    </div>

                    <div className="meter-row">
                      <span>PF</span>
                      <span>{pi.meter?.power_factor?.toFixed(2) ?? "-"}</span>
                    </div>

                    <div className="meter-row">
                      <span>Fwd Energy</span>
                      <span>{pi.meter?.energy_fwd_old_kwh?.toFixed(2) ?? "-"} kWh</span>
                    </div>

                    <div className="meter-row">
                      <span>Rev Energy</span>
                      <span>{pi.meter?.energy_rev_old_kwh?.toFixed(2) ?? "-"} kWh</span>
                    </div>

                    {/* RELAY */}
                    <div className="meter-row">
                      <span>Relay</span>
                      <span className={pi.transfer?.relay_on ? "on" : "off"}>
                        {pi.transfer?.relay_on ? "ON" : "OFF"}
                      </span>
                    </div>

                    {/* TRANSFER */}
                    <div className="meter-row">
                      <span>Transfer</span>
                      <span className={pi.transfer?.active ? "active" : "idle"}>
                        {pi.transfer?.active ? "ACTIVE" : "IDLE"}
                      </span>
                    </div>

                    <div className="meter-row">
                      <span>Threshold Energy</span>
                      <span className={pi.transfer?.threshold_kwh ?.toFixed(2) ?? "-"}>
                        {pi.transfer?.threshold_kwh ?.toFixed(2) ?? "-"}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <table className="meter-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Voltage</th>
              <th>Current</th>
              <th>Power</th>
              <th>PF</th>
              <th>Fwd</th>
              <th>Rev</th>
              <th>Relay</th>
              <th>Transfer</th>
            </tr>
          </thead>

          <tbody>
            {filtered.map((pi) => (
              <tr key={pi.id}>
                <td>{pi.name}</td>
                <td className={pi.status}>{pi.status}</td>

                {pi.status === "online" ? (
                  <>
                    <td>{pi.meter?.voltage_v?.toFixed(1)}</td>
                    <td>{pi.meter?.current_a?.toFixed(2)}</td>
                    <td>{pi.meter?.power_w?.toFixed(0)}</td>
                    <td>{pi.meter?.power_factor?.toFixed(2)}</td>
                    <td>{pi.meter?.energy_fwd_old_kwh?.toFixed(2)}</td>
                    <td>{pi.meter?.energy_rev_old_kwh?.toFixed(2)}</td>
                    <td>{pi.transfer?.relay_on ? "ON" : "OFF"}</td>
                    <td>{pi.transfer?.active ? "ACTIVE" : "IDLE"}</td>
                  </>
                ) : (
                  <td colSpan="9">Offline</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default EnergyDashboardView;


