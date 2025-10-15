// src/components/Navbar/Navbar.jsx
import React, { useState } from "react";
import "./Navbar.css";
import Button from "../Button/Button";
import { registerParticipant } from "../../api/api";
import { Menu } from "lucide-react";

const Navbar = ({ onToggleSidebar }) => {
  const [loading, setLoading] = useState(false);

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

  return (
    <nav className="navbar">
      <div className="nav-left">
        {/* Sidebar Toggle Button */}
        <button className="toggle-btn" onClick={onToggleSidebar}>
          <Menu size={24} />
        </button>

        <img src="/logo.png" alt="Logo" className="logo-img" />
        <h1 className="brand">Energy Trade DApp</h1>
      </div>

      <div className="nav-right">
        <Button text="Register" onClick={handleRegister} loading={loading} />
      </div>
    </nav>
  );
};

export default Navbar;
