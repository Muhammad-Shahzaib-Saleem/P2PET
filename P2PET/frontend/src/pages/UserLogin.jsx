import React from "react";
import { useNavigate } from "react-router-dom";

import LoginForm from "../components/Auth/LoginForm";

const isValidIPv4 = (ip) => {
  if (!ip) return false;
  // quick regex for IPv4 (0-255.0-255.0-255.0-255)
  const re = /^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$/;
  return re.test(ip.trim());
};

const testValidator = () => ({
  ok: true,
  message: "Please enter a valid IPv4 address (e.g., 192.168.0.1)."
});

const UserLoginPage = () => {
  const navigate = useNavigate();

  const handleUserSubmit = async ({ identifier, password }) => {
    // Example: check some userUser item in localStorage for demo
    const stored = localStorage.getItem("normalUser");
    const user = stored ? JSON.parse(stored) : null;

    const savedIp = (user?.ip ?? user?.ipAddress ?? "").trim();
    const savedPass = (user?.password ?? "").trim();

    if (savedIp === (identifier || "").trim() && savedPass === (password || "").trim()) {
      localStorage.setItem("userLoggedIn", "true");
      navigate("/submit-data");
      return true;
    }
    return false;
  };

  return (
    <LoginForm
      role="User"
      onSubmit={handleUserSubmit}
      signupLink="/user-signup"
      submitLabel="Login as User"
      identifierPlaceholder="IP Address"
      identifierType="text"
      validateIdentifier={testValidator}
    />
  );
};

export default UserLoginPage;
