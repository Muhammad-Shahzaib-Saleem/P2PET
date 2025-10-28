import React, { useState } from "react";
import "./RegisterForm.css"; // 👈 import the CSS file

const RegisterForm = ({ onRegister }) => {
  const [hostname, setHostname] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!hostname.trim()) {
      alert("Please enter a hostname");
      return;
    }
    onRegister(hostname);
    setHostname("");
  };

  return (
    <div className="register-container">
      <form onSubmit={handleSubmit} className="register-form">
        <h2 className="form-title">Register Node</h2>

        <div className="form-group">
          <label htmlFor="hostname">Hostname</label>
          <input
            id="hostname"
            type="text"
            value={hostname}
            onChange={(e) => setHostname(e.target.value)}
            placeholder="Enter hostname"
          />
        </div>

        <button type="submit" className="submit-btn">
          Register
        </button>
      </form>
    </div>
  );
};

export default RegisterForm;
