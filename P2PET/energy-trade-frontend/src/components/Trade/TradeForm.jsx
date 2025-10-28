import React, { useState } from "react";
import Button from "../Button/Button";
import { submitTrade } from "../../api/api";
import "./TradeForm.css";

const clampNonNegative = (v) => (v < 0 ? 0 : v);

const TradeForm = () => {
  const [hostname, setHostname] = useState(""); // <-- NEW
  const [role, setRole] = useState("buyer");
  const [energy, setEnergy] = useState("");
  const [price, setPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");

  const to2 = (n) => (Number.isFinite(n) ? Number(n.toFixed(2)) : 0);

  const stepNumber = (setter, current, delta) => {
    const n = parseFloat(current || "0");
    const next = clampNonNegative(n + delta);
    setter(String(to2(next)));
  };

  const onNumChange = (setter) => (e) => {
    const v = e.target.value;
    if (v === "") return setter("");
    const n = parseFloat(v);
    if (Number.isNaN(n)) return;
    setter(String(clampNonNegative(n)));
  };

  const onBlur2 = (setter, value) => {
    if (value === "") return;
    const n = parseFloat(value);
    if (Number.isNaN(n)) return;
    setter(String(to2(clampNonNegative(n))));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setMsg("");

    if (!hostname.trim()) return setMsg("Please enter a hostname.");
    if (!energy || Number(energy) <= 0)
      return setMsg("Enter a valid energy amount.");
    if (!price || Number(price) <= 0)
      return setMsg("Enter a valid price.");

    const normEnergy = to2(parseFloat(energy || "0"));
    const normPrice = to2(parseFloat(price || "0"));

    try {
      setSubmitting(true);
      const res = await submitTrade({
        hostname, // <-- include hostname in payload
        role,
        energy: normEnergy,
        price: normPrice,
      });

      setMsg(res.message || "Trade submitted successfully.");
      setEnergy("");
      setPrice("");
      setHostname("");
    } catch (e) {
      console.error(e);
      setMsg("Failed to submit trade. Check console for details.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="trade-page-center">
      <div className="card trade-card">
        <div className="card-head">
          <h2>Submit Trade</h2>
          <span className="help">
            Provide your hostname, role, energy, and price.
          </span>
        </div>

        <form onSubmit={onSubmit} className="form-grid">

          {/* ✅ Hostname field */}
          <div className="form-row hostname-input">
          <label>Hostname</label>
            <input
              type="text"
              value={hostname}
              onChange={(e) => setHostname(e.target.value)}
              placeholder="e.g. pi_1"
              required
            />
              </div>

          {/* Role */}
          <div className="form-row">
            <label>Role</label>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="buyer">Buyer</option>
              <option value="seller">Seller</option>
            </select>
          </div>

          {/* Energy */}
          <div className="form-row">
            <label>Energy Unit (kWh)</label>
            <div className="number-field">
              <button
                type="button"
                className="stepper-btn"
                aria-label="decrease energy"
                onClick={() => stepNumber(setEnergy, energy, -1)}
              >
                –
              </button>
              <input
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                value={energy}
                onChange={onNumChange(setEnergy)}
                onBlur={() => onBlur2(setEnergy, energy)}
                placeholder="10.53"
                className="number-input"
              />
              <button
                type="button"
                className="stepper-btn"
                aria-label="increase energy"
                onClick={() => stepNumber(setEnergy, energy, +1)}
              >
                +
              </button>
            </div>
          </div>

          {/* Price */}
          <div className="form-row">
            <label>Price</label>
            <div className="number-field">
              <button
                type="button"
                className="stepper-btn"
                aria-label="decrease price"
                onClick={() => stepNumber(setPrice, price, -1)}
              >
                –
              </button>
              <input
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                value={price}
                onChange={onNumChange(setPrice)}
                onBlur={() => onBlur2(setPrice, price)}
                placeholder="15.34"
                className="number-input"
              />
              <button
                type="button"
                className="stepper-btn"
                aria-label="increase price"
                onClick={() => stepNumber(setPrice, price, +1)}
              >
                +
              </button>
            </div>
          </div>

          <div className="form-actions">
            <Button
              type="submit"
              text="Submit Trade"
              loading={submitting}
              full
            />
          </div>
        </form>

        {msg && <div className="form-msg">{msg}</div>}
      </div>
    </div>
  );
};

export default TradeForm;
