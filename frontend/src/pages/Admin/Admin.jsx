import React, { useState } from "react";
import axios from "axios";
import "./Admin.css";

const API_URL = "http://127.0.0.1:5000";

const Admin = () => {
  const [date, setDate] = useState("");
  const [totalWaste, setTotalWaste] = useState("");
  const [servings, setServings] = useState([
    { dish_name: "", quantity: "", image_path: "" },
  ]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleServingChange = (index, field, value) => {
    const updated = [...servings];
    updated[index][field] = value;
    setServings(updated);
  };

  const addServingRow = () => {
    setServings([...servings, { dish_name: "", quantity: "", image_path: "" }]);
  };

  const removeServingRow = (index) => {
    const updated = servings.filter((_, i) => i !== index);
    setServings(
      updated.length
        ? updated
        : [{ dish_name: "", quantity: "", image_path: "" }]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus(null);
    setLoading(true);

    try {
      const payload = {
        date,
        total_waste: parseFloat(totalWaste),
        servings: servings
          .filter((s) => s.dish_name.trim() !== "")
          .map((s) => {
            const base = {
              dish_name: s.dish_name.trim(),
              quantity: parseFloat(s.quantity),
            };
            if (s.image_path && s.image_path.trim() !== "") {
              base.image_path = s.image_path.trim();
            }
            return base;
          }),
      };

      const res = await axios.post(`${API_URL}/add_day`, payload);
      setStatus({ type: "success", message: res.data.message });
      setDate("");
      setTotalWaste("");
      setServings([{ dish_name: "", quantity: "", image_path: "" }]);
    } catch (err) {
      const message =
        err.response?.data?.error || "Failed to add day. Check the data.";
      setStatus({ type: "error", message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin">
      <h2 className="admin-title">Admin Panel</h2>

      <div className="formContainer">
        <form className="admin-form" onSubmit={handleSubmit}>
          <div className="admin-field">
            <label htmlFor="date">Date</label>
            <input
              id="date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          <div className="admin-field">
            <label htmlFor="totalWaste">Total waste (kg)</label>
            <input
              id="totalWaste"
              type="number"
              step="0.01"
              value={totalWaste}
              onChange={(e) => setTotalWaste(e.target.value)}
              required
            />
          </div>

          <div className="admin-servings">
            <div className="admin-servings-header">
              <span>Dish name</span>
              <span>Quantity served</span>
              <span>Image path</span>
              <span />
            </div>

            {servings.map((serving, index) => (
              <div key={index} className="admin-serving-row">
                <input
                  type="text"
                  placeholder="Dish name"
                  value={serving.dish_name}
                  onChange={(e) =>
                    handleServingChange(index, "dish_name", e.target.value)
                  }
                  required
                />
                <input
                  type="number"
                  step="0.1"
                  placeholder="Quantity"
                  value={serving.quantity}
                  onChange={(e) =>
                    handleServingChange(index, "quantity", e.target.value)
                  }
                  required
                />
                <input
                  type="text"
                  placeholder="/images/pizza.png"
                  value={serving.image_path || ""}
                  onChange={(e) =>
                    handleServingChange(index, "image_path", e.target.value)
                  }
                />
                <button
                  type="button"
                  onClick={() => removeServingRow(index)}
                  className="admin-remove-row"
                >
                  ✕
                </button>
              </div>
            ))}

            <button
              type="button"
              onClick={addServingRow}
              className="admin-add-row"
            >
              + Add dish
            </button>
          </div>

          <button type="submit" className="admin-submit" disabled={loading}>
            {loading ? "Saving..." : "Save day"}
          </button>

          {status && (
            <p
              className={
                status.type === "success"
                  ? "admin-status admin-status--success"
                  : "admin-status admin-status--error"
              }
            >
              {status.message}
            </p>
          )}
        </form>
      </div>
    </div>
  );
};

export default Admin;
