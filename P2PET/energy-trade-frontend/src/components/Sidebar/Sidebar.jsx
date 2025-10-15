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
        { key: "submit", label: "Submit Data", path: "/" },
        { key: "hash", label: "Hash Participant", path: "/hash-participant" },
        { key: "execution", label: "Submit Execution Result", path: "/submit-execution-result" },
        { key: "verify", label: "Verify Execution Result", path: "/verify-execution-result" },
        { key: "network", label: "Network Statistics", path: "/network-status" },
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

// // src/components/Sidebar/Sidebar.jsx
// import React from "react";
// import { NavLink } from "react-router-dom";
// import "./Sidebar.css";

// const Sidebar = () => {
//   const sections = [
//     {
//       title: "Transactions",
//       items: [
//         { key: "submit", label: "Submit Data", path: "/" },
//         { key: "hash", label: "Hash Participant", path: "/hash-participant" },
//         { key: "execution", label: "Submit Execution Result", path: "/submit-execution-result" },
//         { key: "verify", label: "Verify Execution Result", path: "/verify-execution-result" },
//         { key: "network", label: "Network Statistics", path: "/network-status" },
//       ],
//     },
//     {
//       title: "Energy",
//       items: [
//         { key: "energy-dashboard", label: "Energy Dashboard", path: "/energy-dashboard" },
//       ],
//     },
//   ];

//   return (
//     <aside className="sidebar">
//       <h2 className="sidebar-title">Menu</h2>

//       {sections.map((section) => (
//         <div className="sidebar-section" key={section.title}>
//           <div className="sidebar-section-title">{section.title}</div>
//           <ul className="sidebar-list">
//             {section.items.map((item) => (
//               <li key={item.key} className="sidebar-item">
//                 <NavLink
//                   to={item.path}
//                   className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
//                   end={item.path === "/"}
//                 >
//                   {item.label}
//                 </NavLink>
//               </li>
//             ))}
//           </ul>
//         </div>
//       ))}
//     </aside>
//   );
// };

// export default Sidebar;
