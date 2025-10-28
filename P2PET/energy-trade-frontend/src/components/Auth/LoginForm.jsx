import React, { useState } from "react";
import { Link } from "react-router-dom";

import Button from "../Button/Button";

import "./Auth.css";

/**
 * Props:
 * - role: "Admin" | "User" (used for labels)
 * - onSubmit: async ({ email, password }) => { ... }  // returns true on success
 * - submitLabel?: string
 * - signupLink?: string (e.g. "/admin-signup" or "/user-signup")
 * - redirectTo?: string (optional, used by page wrappers if they want)
 */
const LoginForm = ({ role = "User", onSubmit, submitLabel, signupLink, identifierPlaceholder = "Email", identifierType = "email", validateIdentifier, }) => {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();

    if (validateIdentifier) {
      const { ok, message } = validateIdentifier(identifier);
      if (!ok) {
        alert(message || "Please enter a valid value.");
        return;
      }
    }

    setLoading(true);
    try {
      const ok = await onSubmit({ identifier: identifier.trim(), password });
      if (!ok) {
        alert("Invalid credentials. Please try again.");
      }
    } catch (err) {
      console.error(err);
      alert(err?.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  // choose autocomplete attr
  const autoComplete = identifierType === "email" ? "email" : identifierType === "text" ? "username" : "off";

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h2>{role} Login</h2>

        <form onSubmit={handleLogin}>
          <input
            type={identifierType === "email" ? "email" : "text"}
            placeholder={identifierPlaceholder}
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
            autoComplete={autoComplete}
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          <Button
            text={submitLabel || "Login"}
            type="submit"
            variant="primary"
            size="md"
            full={true}
            loading={loading}
          />
        </form>

        {signupLink && (
          <p className="auth-note">
            Don't have an account? <Link to={signupLink}>Sign up here</Link>
          </p>
        )}
      </div>
    </div>
  );
};

export default LoginForm;
