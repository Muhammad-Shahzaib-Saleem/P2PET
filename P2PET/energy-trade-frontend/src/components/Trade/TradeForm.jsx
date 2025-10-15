import React, { useState } from "react";
import "./TradeForm.css";
import Button from "../Button/Button";
import { submitTrade } from "../../api/api";

const clampNonNegative = (v) => (v < 0 ? 0 : v);

const TradeForm = () => {
  const [role, setRole] = useState("buyer");
  const [energy, setEnergy] = useState("");
  const [price, setPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState("");

  // keep up to 2 decimals when normalizing
  const to2 = (n) => Number.isFinite(n) ? Number(n.toFixed(2)) : 0;

  // Increment/decrement by exactly 1 (preserves any existing decimals)
  const stepNumber = (setter, current, delta) => {
    const n = parseFloat(current || "0");
    const next = clampNonNegative(n + delta);
    setter(String(to2(next)));
  };

  // onChange for number inputs: allow empty while typing, clamp negatives
  const onNumChange = (setter) => (e) => {
    const v = e.target.value;
    if (v === "") return setter("");
    const n = parseFloat(v);
    if (Number.isNaN(n)) return; // ignore junk
    setter(String(clampNonNegative(n)));
  };

  // onBlur: tidy to 2 decimals
  const onBlur2 = (setter, value) => {
    if (value === "") return;
    const n = parseFloat(value);
    if (Number.isNaN(n)) return;
    setter(String(to2(clampNonNegative(n))));
  };

  const validate = () => {
    if (!energy || Number(energy) <= 0) return "Enter a valid energy amount.";
    if (!price || Number(price) <= 0) return "Enter a valid price.";
    return "";
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setMsg("");

    // normalize before send
    const normEnergy = to2(parseFloat(energy || "0"));
    const normPrice = to2(parseFloat(price || "0"));
    const err =
      normEnergy <= 0
        ? "Enter a valid energy amount."
        : normPrice <= 0
        ? "Enter a valid price."
        : "";

    if (err) return setMsg(err);

    try {
      setSubmitting(true);
      const res = await submitTrade({
        role,
        energy: normEnergy,
        price: normPrice,
      });
      setMsg(res.message || "Trade submitted successfully.");
      setEnergy("");
      setPrice("");
    } catch (e) {
      console.error(e);
      setMsg("Failed to submit trade. Check console for details.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    // Center the card on the page
    <div className="trade-page-center">
      <div className="card trade-card">
        <div className="card-head">
          <h2>Submit Trade</h2>
          <span className="help">
            Provide your role, energy unit, and price.
          </span>
        </div>

        <form onSubmit={onSubmit} className="form-grid">
          {/* Role */}
          <div className="form-row">
            <label>Role</label>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="buyer">Buyer</option>
              <option value="seller">Seller</option>
            </select>
          </div>

          {/* Energy with +/- steppers */}
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

          {/* Price with +/- steppers */}
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
            <Button type="submit" text="Submit Trade" loading={submitting} full />
          </div>
        </form>

        {msg && <div className="form-msg">{msg}</div>}
      </div>
    </div>
  );
};

export default TradeForm;
