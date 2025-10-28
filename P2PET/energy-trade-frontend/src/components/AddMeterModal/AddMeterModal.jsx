// src/components/AddMeterModal/AddMeterModal.jsx
import React, { useEffect, useState } from "react";
import "./AddMeterModal.css";
import Button from "../Button/Button";

/**
 * Props:
 * - onClose: () => void
 * - onSave: (meterData) => void
 * - initialData: optional object with existing meter fields for editing
 * - mode: "add" | "edit" (optional, inferred from initialData if not provided)
 */
const AddMeterModal = ({ onClose, onSave, initialData = null, mode: propMode }) => {
  const inferredMode = propMode || (initialData ? "edit" : "add");
  const [formData, setFormData] = useState({
    meterName: "",
    meterNumber: "",
    fullName: "",
    address: "",
    status: "active",
    installationDate: "",
  });

  // populate form when initialData (edit) arrives, otherwise reset
  useEffect(() => {
    if (initialData) {
      setFormData({
        meterName: initialData.meterName || "",
        meterNumber: initialData.meterNumber || "",
        fullName: initialData.fullName || "",
        address: initialData.address || "",
        status: (initialData.status && initialData.status.toLowerCase()) || "active",
        installationDate: initialData.installationDate || "",
        id: initialData.id ?? undefined,
      });
    } else {
      setFormData({
        meterName: "",
        meterNumber: "",
        fullName: "",
        address: "",
        status: "active",
        installationDate: "",
      });
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((s) => ({ ...s, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Basic validation: ensure required fields present
    if (!formData.meterName || !formData.meterNumber || !formData.fullName) {
      alert("Please fill meter name, meter number and full name.");
      return;
    }

    // Send full object back; parent decides whether to add or update using id
    onSave({
      ...(formData.id ? { id: formData.id } : {}),
      meterName: formData.meterName,
      meterNumber: formData.meterNumber,
      fullName: formData.fullName,
      address: formData.address,
      installationDate: formData.installationDate,
      status: formData.status,
    });

    // close modal after saving
    onClose();
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-box">
        <h3>{inferredMode === "edit" ? "Edit Smart Meter" : "Add New Smart Meter"}</h3>

        <form onSubmit={handleSubmit} className="modal-form">
          {/* show id (read-only) when editing */}
          {inferredMode === "edit" && formData.id && (
            <div className="form-group">
              <label htmlFor="meter-id">Meter ID</label>
              <input
                type="text"
                id="meter-id"
                name="id"
                value={formData.id}
                disabled
                readOnly
                className="disabled-input"
              />
            </div>
          )}

          <input
            type="text"
            name="meterName"
            placeholder="Meter Name"
            value={formData.meterName}
            onChange={handleChange}
            required
            autoFocus
          />

          {/* meterNumber must always be present.
              When editing it is disabled/readOnly; when adding it's editable. */}
          <input
            type="text"
            name="meterNumber"
            placeholder="Meter Number"
            value={formData.meterNumber}
            onChange={handleChange}
            required
            {...(inferredMode === "edit" ? { disabled: true, readOnly: true } : {})}
          />

          <input
            type="text"
            name="fullName"
            placeholder="Full Name"
            value={formData.fullName}
            onChange={handleChange}
            required
          />

          <input
            type="text"
            name="address"
            placeholder="Address"
            value={formData.address}
            onChange={handleChange}
            required
          />

          <input
            type="date"
            name="installationDate"
            placeholder="Installation Date"
            value={formData.installationDate}
            onChange={handleChange}
            required
          />

          <select name="status" value={formData.status} onChange={handleChange} required>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>

          <div className="modal-actions">
            <Button
              text={inferredMode === "edit" ? "Save Changes" : "Save Meter"}
              type="submit"
              variant="primary"
              size="md"
            />
            <Button text="Cancel" type="button" variant="secondary" size="md" onClick={onClose} />
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddMeterModal;
