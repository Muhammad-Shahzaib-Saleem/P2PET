// src/components/Sidebar/Sidebar.jsx
import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { FiChevronDown, FiChevronRight } from "react-icons/fi"; // arrow icons

import "./Sidebar.css";

const Sidebar = () => {
  const [openSection, setOpenSection] = useState(null); // track which is expanded

  const sections = [
    {
      title: "Transactions",
      key: "transactions",
      items: [
        { key: "register", label: "Register Node", path: "/register-node" },
        { key: "submit", label: "Submit Data", path: "/submit-data" },
        { key: "hash", label: "Hash Participant", path: "/hash-participant" },
        { key: "execution", label: "Submit Execution Result", path: "/submit-execution-result" },
        { key: "advance", label: "Advance Phase", path: "/advance-phase" },
        { key: "verify", label: "Verify Execution Result", path: "/verify-execution-result" },
        { key: "network", label: "Market Status", path: "/network-status" },
      ],
    },
    {
      title: "Bidding Results",
      key: "Results Matching Prosumer and Consumer",
      items: [
        { key: "Bidding Result", label: "Bidding Result", path: "/bidding-result" },
      ],
    },
    {
      title: "Energy",
      key: "energy",
      items: [
        { key: "energy-dashboard", label: "Energy Dashboard", path: "/energy-dashboard" },
      ],
    },
  ];

  const toggleSection = (key) => {
    setOpenSection(openSection === key ? null : key);
  };

  return (
    <aside className="sidebar">
      <h2 className="sidebar-title">Menu</h2>

      {sections.map((section) => (
        <div
          className="sidebar-section"
          key={section.key}
        >
          {/* Section Header with Hover Arrow */}
          <div
            className="sidebar-section-header"
            onClick={() => toggleSection(section.key)}
          >
            <span>{section.title}</span>
            <span className="arrow">
              {openSection === section.key ? <FiChevronDown /> : <FiChevronRight />}
            </span>
          </div>

          {/* Show items only if expanded */}
          {openSection === section.key && (
            <ul className="sidebar-list">
              {section.items.map((item) => (
                <li key={item.key} className="sidebar-item">
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      `sidebar-link ${isActive ? "active" : ""}`
                    }
                    end={item.path === "/"}
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </aside>
  );
};

export default Sidebar;
