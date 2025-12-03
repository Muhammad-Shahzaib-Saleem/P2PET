// src/components/Button/Button.jsx
import React from "react";
import "./Button.css";

const Button = ({
  text,
  type = "button",
  onClick,
  variant = "primary", // primary | secondary | danger
  size = "md", // sm | md | lg
  loading = false,
  disabled = false,
  full = false,
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`btn btn-${variant} btn-${size} ${full ? "btn-full" : ""}`}
      aria-busy={loading ? "true" : "false"}
    >
      {loading ? "Please wait..." : text}
    </button>
  );
};

export default Button;
