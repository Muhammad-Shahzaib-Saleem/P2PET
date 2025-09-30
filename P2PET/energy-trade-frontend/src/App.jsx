// src/App.jsx
import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/NavBar/Navbar";
import Sidebar from "./components/Sidebar/Sidebar";
import SubmitData from "./pages/SubmitData";
import HashParticipant from "./pages/HashParticipant";
import NetworkStatus from "./pages/NetworkStatus";
import SubmitExecutionResultPage from "./pages/SubmitExecutionResultPage";
import VerifyExecutionResult from "./pages/VerifyExecutionResult";
import EnergyDashboard from "./pages/EnergyDashboard";
import "./App.css";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true); // default: open

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  return (
    <div className="app-container">
      <Navbar onToggleSidebar={toggleSidebar} />

      <div className="main-layout">
        {sidebarOpen && <Sidebar />}
        <div className="content-area">
          <Routes>
            <Route path="/" element={<SubmitData />} />
            <Route path="/hash-participant" element={<HashParticipant />} />
            <Route path="/submit-execution-result" element={<SubmitExecutionResultPage />} />
            <Route path="/verify-execution-result" element={<VerifyExecutionResult />} />
            <Route path="/network-status" element={<NetworkStatus />} />
            <Route path="/energy-dashboard" element={<EnergyDashboard />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default App;
