import React, { useState } from "react";
import { Link } from "react-router-dom";

import Button from "../Button/Button";

import "./Auth.css";

const SignupForm = ({ role, fields, onSubmit, loginLink }) => {
  // initialize state for all fields dynamically
  const [formData, setFormData] = useState(
    fields.reduce((acc, field) => {
      acc[field.name] = "";
      return acc;
    }, {})
  );

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    // password confirmation check if fields exist
    if (formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword) {
      alert("Passwords do not match. Please try again.");
      return;
    }

    const ok = await onSubmit(formData);
    if (ok) {
      alert(`${role} registered successfully. Please log in.`);
    } else {
      alert("Signup failed. Try again.");
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h2>{role} Signup</h2>
        <form onSubmit={handleSignup}>
          {fields.map((field) => (
            <input
              key={field.name}
              type={field.type}
              name={field.name}
              placeholder={field.placeholder}
              value={formData[field.name]}
              onChange={handleChange}
              required={field.required}
              minLength={field.minLength}
              autoComplete={field.autoComplete || "off"}
            />
          ))}

          <Button
            text="Sign up"
            type="submit"
            variant="primary"
            size="md"
            full={true}
          />
        </form>

        {loginLink && (
          <p className="auth-note">
            Already registered? <Link to={loginLink}>Login here</Link>
          </p>
        )}
      </div>
    </div>
  );
};

export default SignupForm;
