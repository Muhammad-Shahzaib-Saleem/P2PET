// src/components/ViewToggle/ViewToggle.jsx
import React from "react";
import "./ViewToggle.css";

/**
 * Props:
 * - viewMode: "cards" | "table"
 * - onToggle: () => void
 */
const TableIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden>
    <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
    <path d="M3 10h18" stroke="currentColor" strokeWidth="1.5" />
  </svg>
);

const CardIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden>
    <rect x="3.5" y="4.5" width="17" height="15" rx="2" stroke="currentColor" strokeWidth="1.5" />
    <rect x="7" y="8" width="10" height="3" rx="1" fill="currentColor" />
  </svg>
);

const ViewToggle = ({ viewMode = "cards", onToggle }) => {
  const show = viewMode === "cards" ? "table" : "cards"; // show the view we will switch to
  return (
    <button className="view-toggle-btn" onClick={onToggle} title={`Switch to ${show} view`}>
      {viewMode === "cards" ? <TableIcon /> : <CardIcon />}
      <span className="view-toggle-label">{viewMode === "cards" ? "Table" : "Cards"}</span>
    </button>
  );
};

export default ViewToggle;
