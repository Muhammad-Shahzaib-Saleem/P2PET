// src/components/Navbar/Navbar.jsx
import React, { useState } from "react";
import { Menu } from "lucide-react";
import { useNavigate } from "react-router-dom";

import Button from "../Button/Button";
import { registerParticipant } from "../../api/api";

import "./Navbar.css";

const Navbar = ({ onToggleSidebar, showToggle = true }) => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      setLoading(true);
      const res = await registerParticipant();
      alert(res.message || "Registered successfully!");
    } catch (e) {
      console.error(e);
      alert("Registration failed. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogoClick = () => {
    navigate("/");
  };

  return (
    <nav className={`navbar ${showToggle ? "" : "navbar--no-toggle"}`}>
      <div className="nav-left">
        {showToggle && (
          <button
            className="toggle-btn"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <Menu size={24} />
          </button>
        )}

        <div
          className="brand-container"
          onClick={handleLogoClick}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && handleLogoClick()}
        >
          <img src="/logo.png" alt="Logo" className="logo-img" />
          <h1 className="brand">Energy Trade DApp</h1>
        </div>
      </div>

      {/* <div className="nav-right">
        <Button text="Register" onClick={handleRegister} loading={loading} />
      </div> */}
    </nav>
  );
};

export default Navbar;
