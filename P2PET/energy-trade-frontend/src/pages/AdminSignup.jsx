import React from "react";
import { useNavigate } from "react-router-dom";

import SignupForm from "../components/Auth/SignupForm";

const AdminSignupPage = () => {
  const navigate = useNavigate();

  const handleAdminSignup = async (formData) => {
    // store the admin info in localStorage
    localStorage.setItem("adminUser", JSON.stringify(formData));
    navigate("/admin-login");
    return true;
  };

  return (
    <SignupForm
      role="Admin"
      fields={[
        { name: "firstName", type: "text", placeholder: "First Name", required: true },
        { name: "lastName", type: "text", placeholder: "Last Name", required: true },
        { name: "dob", type: "date", placeholder: "Date of Birth", required: true },
        { name: "email", type: "email", placeholder: "Email", required: true, autoComplete: "email" },
        { name: "password", type: "password", placeholder: "Password (min 6 chars)", required: true, minLength: 6 },
        { name: "confirmPassword", type: "password", placeholder: "Confirm Password", required: true, minLength: 6 },
      ]}
      onSubmit={handleAdminSignup}
      loginLink="/admin-login"
    />
  );
};

export default AdminSignupPage;
