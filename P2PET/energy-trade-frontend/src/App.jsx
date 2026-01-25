// src/App.jsx
import React, { useEffect, useState } from "react";
import { Routes, Route, useLocation } from "react-router-dom";

import Navbar from "./components/NavBar/Navbar";
import Sidebar from "./components/Sidebar/Sidebar";
import ChatBot from "./components/ChatBot/ChatBot";
import SubmitData from "./pages/SubmitData";
import HashParticipant from "./pages/HashParticipant";
import NetworkStatus from "./pages/NetworkStatus";
import SubmitExecutionResultPage from "./pages/SubmitExecutionResultPage";
import VerifyExecutionResult from "./pages/VerifyExecutionResult";
import EnergyDashboard from "./pages/EnergyDashboard";
import HomePage from "./pages/HomePage";
import AdminLoginPage from "./pages/AdminLogin";
import AdminSignupPage from "./pages/AdminSignup";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import UserLoginPage from "./pages/UserLogin";
import UserSignupPage from "./pages/UserSignupPage";
import RegisterNode from "./pages/RegisterNode";
import AdvancePhase from "./pages/AdvancePhase";

import "./App.css";

function App() {
  const location = useLocation();

  const MQ = "(max-width: 920px)";
  const isMobileInitial = window.matchMedia(MQ).matches;

  // Start: mobile -> closed, desktop -> open
  const [isMobile, setIsMobile] = useState(isMobileInitial);
  const [sidebarOpen, setSidebarOpen] = useState(!isMobileInitial);

  useEffect(() => {
    const mm = window.matchMedia(MQ);
    const handler = (e) => {
      setIsMobile(e.matches);
      setSidebarOpen(e.matches ? false : true); // enter mobile: close, desktop: open
    };
    handler(mm); // run once to be safe
    mm.addEventListener("change", handler);
    return () => mm.removeEventListener("change", handler);
  }, []);

  // Close drawer when navigating on mobile
  useEffect(() => {
    if (isMobile) setSidebarOpen(false);
  }, [location.pathname, isMobile]);

  const toggleSidebar = () => setSidebarOpen((s) => !s);

  const minimalRoutes = ["/", "/admin-login", "/admin-signup", "/user-login", "/user-signup", "/admin-dashboard"];
  const isMinimalPage = minimalRoutes.includes(location.pathname);

  const showToggle = !isMinimalPage;

  // IMPORTANT: now the sidebar exists only when sidebarOpen is true (desktop & mobile)
  const showSidebar = !isMinimalPage && sidebarOpen;

  return (
    <div className="app-container">
      <Navbar onToggleSidebar={toggleSidebar} showToggle={showToggle} />

      <div
        className={`main-layout ${isMobile ? "is-mobile" : ""} ${
          sidebarOpen ? "sidebar-open" : ""
        }`}
      >
        {showSidebar && <Sidebar />}

        {isMobile && sidebarOpen && !isMinimalPage && (
          <div
            className="sidebar-backdrop"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <div className="content-area">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/admin-login" element={<AdminLoginPage />} />
            <Route path="/admin-signup" element={<AdminSignupPage />} />
            <Route path="/user-login" element={<UserLoginPage />} />
            <Route path="/user-signup" element={<UserSignupPage />} />
            <Route path="/admin-dashboard" element={<AdminDashboardPage />} />
            <Route path="/register-node" element={<RegisterNode />} />
            <Route path="/submit-data" element={<SubmitData />} />
            <Route path="/hash-participant" element={<HashParticipant />} />
            <Route
              path="/submit-execution-result"
              element={<SubmitExecutionResultPage />}
            />
            <Route path="/advance-phase" element={<AdvancePhase />} />
            <Route
              path="/verify-execution-result"
              element={<VerifyExecutionResult />}
            />
            <Route path="/network-status" element={<NetworkStatus />} />
            <Route path="/energy-dashboard" element={<EnergyDashboard />} />
          </Routes>
        </div>
      </div>

      {/* AI Chatbot - Available on all pages */}
      <ChatBot />
    </div>
  );
}

export default App;

// // src/App.jsx
// import React, { useState } from "react";
// import { Routes, Route, useLocation } from "react-router-dom";

// import Navbar from "./components/NavBar/Navbar";
// import Sidebar from "./components/Sidebar/Sidebar";
// import SubmitData from "./pages/SubmitData";
// import HashParticipant from "./pages/HashParticipant";
// import NetworkStatus from "./pages/NetworkStatus";
// import SubmitExecutionResultPage from "./pages/SubmitExecutionResultPage";
// import VerifyExecutionResult from "./pages/VerifyExecutionResult";
// import EnergyDashboard from "./pages/EnergyDashboard";
// import HomePage from "./pages/HomePage";
// import AdminLoginPage from "./pages/AdminLogin";
// import AdminSignupPage from "./pages/AdminSignup";
// import AdminDashboardPage from "./pages/AdminDashboardPage";
// import UserLoginPage from "./pages/UserLogin";
// import UserSignupPage from "./pages/UserSignupPage";

// import "./App.css";

// function App() {
//   const [sidebarOpen, setSidebarOpen] = useState(true); // default: open

//   // const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
//   const toggleSidebar = () => setSidebarOpen((s) => !s);

//   const location = useLocation();
//   const minimalRoutes = [
//     "/",
//     "/admin-login",
//     "/admin-signup",
//     "/user-login",
//     "/user-signup",
//     "/admin-dashboard",
//   ];

//   // Determine whether current path is one of the minimal pages
//   const isMinimalPage = minimalRoutes.includes(location.pathname);

//   // only show sidebar when not on minimal pages and sidebarOpen is true
//   const shouldShowSidebar = !isMinimalPage && sidebarOpen;

//   return (
//     <div className="app-container">
//       <Navbar onToggleSidebar={toggleSidebar} showToggle={!isMinimalPage} />

//       <div className="main-layout">
//         {shouldShowSidebar && <Sidebar />}
//         <div className="content-area">
//           <Routes>
//             <Route path="/" element={<HomePage />} />
//             <Route path="/admin-login" element={<AdminLoginPage />} />
//             <Route path="/admin-signup" element={<AdminSignupPage />} />
//             <Route path="/user-login" element={<UserLoginPage />} />
//             <Route path="/user-signup" element={<UserSignupPage />} />
//             <Route path="/admin-dashboard" element={<AdminDashboardPage />} />
//             <Route path="/submit-data" element={<SubmitData />} />
//             <Route path="/hash-participant" element={<HashParticipant />} />
//             <Route path="/submit-execution-result" element={<SubmitExecutionResultPage />} />
//             <Route path="/verify-execution-result" element={<VerifyExecutionResult />} />
//             <Route path="/network-status" element={<NetworkStatus />} />
//             <Route path="/energy-dashboard" element={<EnergyDashboard />} />
//           </Routes>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default App;
