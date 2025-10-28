// src/components/MeterTable/MeterTable.jsx
import React from "react";
import Button from "../Button/Button";
import "./MeterTable.css";

/**
 * Props:
 * - meters: array
 * - onEdit: (meter) => void
 * - onRemove: (id) => void
 */
const MeterTable = ({ meters = [], onEdit, onRemove }) => {
  return (
    <div className="meter-table-wrap">
      <table className="meter-table">
        <thead>
          <tr>
            <th>Meter Name</th>
            <th>Meter #</th>
            <th>Full Name</th>
            <th>Address</th>
            <th>Installation</th>
            <th>Status</th>
            <th style={{ width: 150 }}>Actions</th>
          </tr>
        </thead>

        <tbody>
          {meters.map((m) => (
            <tr key={m.id}>
              <td>{m.meterName}</td>
              <td>{m.meterNumber}</td>
              <td>{m.fullName}</td>
              <td>{m.address}</td>
              <td>{m.installationDate}</td>
              <td>
                <span className={`status-pill ${String(m.status || "active").toLowerCase()}`}>
                  {m.status}
                </span>
              </td>
              <td className="table-actions">
                <Button text="Edit" size="sm" onClick={() => onEdit(m)} variant="primary" />
                <Button text="Remove" size="sm" onClick={() => onRemove(m.id)} variant="danger" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MeterTable;
