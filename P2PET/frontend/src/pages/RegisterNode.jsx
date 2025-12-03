// src/pages/RegisterNode.jsx
import React from "react";
import RegisterForm from "../components/Register/RegisterForm";

const RegisterNode = () => {
  const handleRegister = (hostname) => {
    console.log("Registering hostname:", hostname);
    // Later, you can call your backend API here, for example:
    // fetch("/api/register-hostname", { method: "POST", body: JSON.stringify({ hostname }) });
  };

  return <RegisterForm onRegister={handleRegister} />;
};

export default RegisterNode;
