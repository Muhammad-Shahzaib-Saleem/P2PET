import React from "react";
import EnergyDualBar from "./EnergyDualBar";

const EnergyHourlyModal = ({ open, dayLabel, rows, onClose }) => {
  if (!open) return null;

  return (
    <div className="ct-modal-backdrop" onClick={onClose}>
      <div className="ct-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ct-modal-header">
          <h4 style={{ margin: 0 }}>{dayLabel} — hourly energy</h4>
          <button className="ct-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="ct-modal-body">
          <div className="ct-modal-chart">
            {/* Same look as weekly, just with "Hour" on the x-axis */}
            <EnergyDualBar data={rows} xLabel="Hour" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnergyHourlyModal;
