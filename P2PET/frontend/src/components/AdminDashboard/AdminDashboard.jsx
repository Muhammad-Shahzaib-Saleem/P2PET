// src/components/AdminDashboard/AdminDashboard.jsx
import React, { useState } from "react";

import Button from "../Button/Button";
import AddMeterModal from "../AddMeterModal/AddMeterModal";
import SearchBar from "../SearchBar/SearchBar";
import ViewToggle from "../ViewToggle/ViewToggle";
import MeterTable from "../MeterTable/MeterTable";

import "./AdminDashboard.css";

const AdminDashboard = () => {
  const [meters, setMeters] = useState([
    {
      id: 1,
      meterName: "Main Building Meter",
      meterNumber: "SM-001",
      fullName: "John Doe",
      address: "123 Solar Street, Karachi",
      installationDate: "2024-08-15",
      status: "active",
    },
    {
      id: 2,
      meterName: "Backup Generator Meter",
      meterNumber: "SM-002",
      fullName: "Alice Smith",
      address: "45 Wind Avenue, Lahore",
      installationDate: "2024-09-02",
      status: "inactive",
    },
    {
      id: 3,
      meterName: "SSE Building Meter",
      meterNumber: "SM-003",
      fullName: "SBSSE",
      address: "123 Solar Street, Lahore",
      installationDate: "2024-08-25",
      status: "active",
    },
    {
      id: 4,
      meterName: "SDSB Building Meter",
      meterNumber: "SM-004",
      fullName: "Business",
      address: "DHA, Lahore",
      installationDate: "2024-07-12",
      status: "active",
    },
    {
      id: 5,
      meterName: "PDC Building Meter",
      meterNumber: "SM-005",
      fullName: "Pepsi Dinning Center",
      address: "DHA Phase 5, Lahore",
      installationDate: "2025-09-05",
      status: "active",
    },
    {
      id: 6,
      meterName: "MGSHSS Building Meter",
      meterNumber: "SM-006",
      fullName: "Management Sciences",
      address: "LUMS, Lahore",
      installationDate: "2025-04-12",
      status: "inactive",
    },
    {
      id: 7,
      meterName: "Academic Building Meter",
      meterNumber: "SM-007",
      fullName: "Main Building",
      address: "LUMS Phase 5, Lahore",
      installationDate: "2025-01-24",
      status: "active",
    },
    {
      id: 8,
      meterName: "Faculty Building Meter",
      meterNumber: "SM-008",
      fullName: "Residential Area",
      address: "LUMS, Lahore",
      installationDate: "2025-02-21",
      status: "inactive",
    },
    {
      id: 9,
      meterName: "Law Building Meter",
      meterNumber: "SM-000",
      fullName: "Gurmani School",
      address: "LUMS Phase 5, Lahore",
      installationDate: "2025-07-27",
      status: "active",
    },
    {
      id: 10,
      meterName: "Sports Complex Building",
      meterNumber: "SM-010",
      fullName: "Coca Cola SC",
      address: "LUMS, Lahore",
      installationDate: "2025-02-21",
      status: "inactive",
    },
  ]);

  const [filteredMeters, setFilteredMeters] = useState(meters);
  const [showModal, setShowModal] = useState(false);
  const [editingMeter, setEditingMeter] = useState(null);
  const [viewMode, setViewMode] = useState("cards"); // "cards" | "table"
  const [searchActive, setSearchActive] = useState(false);

  const handleSearch = (query) => {
    if (!query.trim()) {
      setFilteredMeters(meters);
    } else {
      const lowerQuery = query.toLowerCase();
      setFilteredMeters(
        meters.filter(
          (m) =>
            m.meterName.toLowerCase().includes(lowerQuery) ||
            m.meterNumber.toLowerCase().includes(lowerQuery) ||
            m.fullName.toLowerCase().includes(lowerQuery) ||
            m.address.toLowerCase().includes(lowerQuery)
        )
      );
    }
  };

  const handleAddMeter = (meter) => {
    const normalized = { ...meter, status: (meter.status || "active").toLowerCase() };
    if (editingMeter && editingMeter.id) {
      const updated = meters.map((m) =>
        m.id === (meter.id ?? editingMeter.id) ? { ...m, ...normalized } : m
      );
      setMeters(updated);
      setFilteredMeters(updated);
      setEditingMeter(null);
    } else {
      const newMeters = [...meters, { id: Date.now(), ...normalized }];
      setMeters(newMeters);
      setFilteredMeters(newMeters);
    }
  };

  const handleRemove = (id) => {
    if (window.confirm("Are you sure you want to remove this meter?")) {
      const updated = meters.filter((m) => m.id !== id);
      setMeters(updated);
      setFilteredMeters(updated);
    }
  };

  const handleEdit = (meter) => {
    setEditingMeter(meter);
    setShowModal(true);
  };

  const openAddModal = () => {
    setEditingMeter(null);
    setShowModal(true);
  };

  const toggleView = () => setViewMode((v) => (v === "cards" ? "table" : "cards"));

  return (
    <div className={`dashboard-container ${searchActive ? "search-active" : ""}`}>
      <div className="dashboard-header">
        <h1 className="dashboard-title">Admin Dashboard</h1>

        <div className="header-controls" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* pass onActiveChange to notify parent when search opens/closes */}
          <SearchBar onSearch={handleSearch} onActiveChange={(active) => setSearchActive(active)} />

          {/* hide view toggle on mobile while search is active; CSS will handle it via .search-active class */}
          <div className="hide-on-search">
            <ViewToggle viewMode={viewMode} onToggle={toggleView} />
          </div>

          {/* Add button wrapper so we can hide it when search is active on mobile */}
          <div className="hide-on-search">
            <Button text="Add New Meter" onClick={openAddModal} variant="primary" size="md" />
          </div>
        </div>
      </div>

      {filteredMeters.length === 0 ? (
        <div className="empty-state">No meters found.</div>
      ) : viewMode === "cards" ? (
        <div className="meter-list">
          {filteredMeters.map((meter) => (
            <div className="meter-card" key={meter.id}>
              <div className="meter-actions">
                <Button text="Edit" size="sm" onClick={() => handleEdit(meter)} variant="primary" />
                <Button text="Remove" size="sm" onClick={() => handleRemove(meter.id)} variant="danger" />
              </div>

              <div className="meter-details">
                <h3 className="meter-name">{meter.meterName}</h3>
                <div className="meter-row">
                  <span className="meter-label">Meter #</span>
                  <span>{meter.meterNumber}</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Full Name</span>
                  <span>{meter.fullName}</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Address</span>
                  <span>{meter.address}</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Installation</span>
                  <span>{meter.installationDate}</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Status</span>
                  <span className={`status ${meter.status?.toLowerCase()}`}>{meter.status}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <MeterTable meters={filteredMeters} onEdit={handleEdit} onRemove={handleRemove} />
      )}

      {showModal && (
        <AddMeterModal
          onClose={() => {
            setShowModal(false);
            setEditingMeter(null);
          }}
          onSave={handleAddMeter}
          initialData={editingMeter || null}
        />
      )}
    </div>
  );
};

export default AdminDashboard;
