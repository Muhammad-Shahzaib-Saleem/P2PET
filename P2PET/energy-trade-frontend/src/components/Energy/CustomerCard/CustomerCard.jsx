import React from "react";
import "./CustomerCard.css";

const CustomerCard = ({ data }) => {
  if (!data) return null;

  return (
    <div className="cc-card">
      <div className="cc-header">
        <h3>Customer Detail</h3>
      </div>
      <div className="cc-body">
        <div className="cc-grid2">
          <div className="cc-field">
            <div className="cc-label">Name</div>
            <div className="cc-value">{data.name}</div>
          </div>
          <div className="cc-field">
            <div className="cc-label">Customer ID</div>
            <div className="cc-value">{data.id}</div>
          </div>
          <div className="cc-field">
            <div className="cc-label">Utility</div>
            <div className="cc-value">{data.utility}</div>
          </div>
          <div className="cc-field">
            <div className="cc-label">Meter ID</div>
            <div className="cc-value">{data.meterId}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerCard;
