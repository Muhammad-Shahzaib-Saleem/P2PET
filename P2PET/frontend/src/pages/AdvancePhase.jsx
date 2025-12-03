// src/pages/RegisterNode.jsx
import React from "react";
import RegisterForm from "../components/Register/RegisterForm";
import AdvancePhaseForm from "../components/AdvancePhase/AdvancePhaseForm"; 

const AdvancePhase = () => {
  const handleAdvancePhase = (hostname) => {
    console.log("Enter hostname for changing phase:", hostname);
    // Later, you can call your backend API here, for example:
    // fetch("/api/register-hostname", { method: "POST", body: JSON.stringify({ hostname }) });
  };

  return <AdvancePhaseForm onRegister={handleAdvancePhase} />;
};

export default AdvancePhase;
