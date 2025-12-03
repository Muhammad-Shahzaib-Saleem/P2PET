import React from "react";
import { useNavigate } from "react-router-dom";

import SignupForm from "../components/Auth/SignupForm";

const UserSignupPage = () => {
  const navigate = useNavigate();

  const handleUserSignup = async (formData) => {
    const toStore = {
      ip: (formData.ipAddress || "").trim(),
      password: (formData.password || "").trim(),
    };
    localStorage.setItem("normalUser", JSON.stringify(toStore));
    navigate("/submit-data");
    return true;
  };

  return (
    <SignupForm
      role="User"
      fields={[
        { name: "ipAddress", type: "text", placeholder: "IP Address", required: true },
        { name: "password", type: "password", placeholder: "Password (min 6 chars)", required: true, minLength: 6 },
        { name: "confirmPassword", type: "password", placeholder: "Confirm Password", required: true, minLength: 6 },
      ]}
      onSubmit={handleUserSignup}
      loginLink="/user-login"
    />
  );
};

export default UserSignupPage;
