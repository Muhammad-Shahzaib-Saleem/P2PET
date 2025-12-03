import React from "react";
import { useNavigate } from "react-router-dom";

import LoginForm from "../components/Auth/LoginForm";

const AdminLoginPage = () => {
  const navigate = useNavigate();

  const handleAdminSubmit = async ({ identifier, password }) => {
    // Demo approach (existing localStorage logic)
    const stored = localStorage.getItem("adminUser");
    const admin = stored ? JSON.parse(stored) : null;

    if (admin && admin.email === identifier && admin.password === password) {
      localStorage.setItem("adminLoggedIn", "true");
      // return true so LoginForm won't show generic alert
      navigate("/admin-dashboard"); // or /submit-execution-result as you used
      return true;
    }
    return false;
  };

  return (
    <LoginForm
      role="Admin"
      onSubmit={handleAdminSubmit}
      signupLink="/admin-signup"
      submitLabel="Login as Admin"
      identifierPlaceholder="Email"
      identifierType="email"
    />
  );
};

export default AdminLoginPage;
