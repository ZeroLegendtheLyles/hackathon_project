import React, { useEffect, useState } from "react";
import axios from "axios";
import "./OptimizeMenu.css";

const API_URL = "http://127.0.0.1:5001";

const OptimizeMenu = () => {
  const [dishes, setDishes] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [constraints, setConstraints] = useState({});
  const [totalMin, setTotalMin] = useState(80);
  const [totalMax, setTotalMax] = useState(120);
  const [numDishes, setNumDishes] = useState(3);

  const [requirements, setRequirements] = useState({
    require_staple: true,
    require_vegetable: true,
    require_protein: false,
    require_dairy: false,
  });

  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchDishes = async () => {
    try {
      const res = await axios.get(`${API_URL}/dishes_waste_rates`, {
        params: { sort: "desc", order_by: "waste_rate" },
      });
      const list = res.data.dishes || [];
      setDishes(list);
      setSelectedIds(list.map((d) => d.id));

      const baseConstraints = {};
      list.forEach((d) => {
        baseConstraints[d.id] = { min: 5, max: 30 };
      });
      setConstraints(baseConstraints);
    } catch (e) {
      console.error(e);
      setDishes([]);
    }
  };

  useEffect(() => {
    fetchDishes();
  }, []);

  const toggleDishSelected = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleConstraintChange = (id, field, value) => {
    setConstraints((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [field]: value,
      },
    }));
  };

  const handleRequirementToggle = (field) => {
    setRequirements((prev) => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const dishConstraintsPayload = {};
      Object.entries(constraints).forEach(([id, c]) => {
        dishConstraintsPayload[String(id)] = {
          min: Number(c.min),
          max: Number(c.max),
        };
      });

      const payload = {
        total_quantity_range: [Number(totalMin), Number(totalMax)],
        num_dishes: Number(numDishes),
        dish_constraints: dishConstraintsPayload,
        category_requirements: requirements,
        available_dishes: selectedIds,
      };

      const res = await axios.post(`${API_URL}/optimize_menu`, payload);
      setResult(res.data.optimization_result);
    } catch (e) {
      console.error(e);
      const msg =
        e.response?.data?.error ||
        "Failed to optimize menu. Check constraints.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="optimize">
      <h2 className="optimize-title">Menu Optimizer</h2>

      <section className="optimize-grid">
        <form className="optimize-card" onSubmit={handleSubmit}>
          <h3 className="optimize-card-title">Constraints</h3>

          <div className="optimize-field-row">
            <div className="optimize-field">
              <label>Total quantity min (kg)</label>
              <input
                type="number"
                value={totalMin}
                onChange={(e) => setTotalMin(e.target.value)}
              />
            </div>
            <div className="optimize-field">
              <label>Total quantity max (kg)</label>
              <input
                type="number"
                value={totalMax}
                onChange={(e) => setTotalMax(e.target.value)}
              />
            </div>
          </div>

          <div className="optimize-field">
            <label>Number of dishes in optimized menu</label>
            <input
              type="number"
              min="1"
              value={numDishes}
              onChange={(e) => setNumDishes(e.target.value)}
            />
          </div>

          <div className="optimize-field">
            <label>Category requirements</label>
            <div className="optimize-checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={requirements.require_staple}
                  onChange={() => handleRequirementToggle("require_staple")}
                />
                Staple
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={requirements.require_vegetable}
                  onChange={() => handleRequirementToggle("require_vegetable")}
                />
                Vegetable
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={requirements.require_protein}
                  onChange={() => handleRequirementToggle("require_protein")}
                />
                Protein
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={requirements.require_dairy}
                  onChange={() => handleRequirementToggle("require_dairy")}
                />
                Dairy
              </label>
            </div>
          </div>

          <div className="optimize-dish-table">
            <div className="optimize-dish-header">
              <span>Use</span>
              <span>Dish</span>
              <span>Waste rate</span>
              <span>Min qty</span>
              <span>Max qty</span>
            </div>
            {dishes.map((dish) => {
              const c = constraints[dish.id] || { min: "", max: "" };
              return (
                <div key={dish.id} className="optimize-dish-row">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(dish.id)}
                    onChange={() => toggleDishSelected(dish.id)}
                  />
                  <span className="optimize-dish-name">{dish.name}</span>
                  <span className="optimize-dish-waste">
                    {(dish.waste_rate * 100).toFixed(1)}%
                  </span>
                  <input
                    type="number"
                    value={c.min}
                    onChange={(e) =>
                      handleConstraintChange(dish.id, "min", e.target.value)
                    }
                  />
                  <input
                    type="number"
                    value={c.max}
                    onChange={(e) =>
                      handleConstraintChange(dish.id, "max", e.target.value)
                    }
                  />
                </div>
              );
            })}
          </div>

          <button type="submit" className="optimize-submit" disabled={loading}>
            {loading ? "Optimizing..." : "Run optimization"}
          </button>

          {error && <p className="optimize-error">{error}</p>}
        </form>

        <div className="optimize-card">
          <h3 className="optimize-card-title">Result</h3>
          {!result && !error && (
            <p className="optimize-placeholder">
              Set constraints and run the optimizer to see a suggested menu.
            </p>
          )}

          {result && (
            <div className="optimize-result">
              <div className="optimize-result-summary">
                <div>
                  <span className="optimize-result-label">Total quantity</span>
                  <span className="optimize-result-value">
                    {result.total_quantity} kg
                  </span>
                </div>
                <div>
                  <span className="optimize-result-label">Predicted waste</span>
                  <span className="optimize-result-value">
                    {result.total_predicted_waste} kg
                  </span>
                </div>
                <div>
                  <span className="optimize-result-label">Waste rate</span>
                  <span className="optimize-result-value">
                    {(result.waste_rate * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <ul className="optimize-result-list">
                {result.selected_dishes.map((d) => (
                  <li key={d.dish_id} className="optimize-result-item">
                    <div className="optimize-result-main">
                      <div className="optimize-result-img-wrapper">
                        <img
                          src={`${API_URL}${d.image_path}`}
                          alt={d.dish_name}
                        />
                      </div>
                      <div className="optimize-result-text">
                        <span className="optimize-result-name">
                          {d.dish_name}
                        </span>
                        <span className="optimize-result-category">
                          {d.category}
                        </span>
                      </div>
                    </div>
                    <div className="optimize-result-meta">
                      <span>{d.quantity} kg</span>
                      <span>{d.predicted_waste} kg waste</span>
                    </div>
                  </li>
                ))}
              </ul>

              <p className="optimize-status-text">
                Solver status: {result.optimization_status}
              </p>
            </div>
          )}

          {error && !result && <p className="optimize-error-bottom">{error}</p>}
        </div>
      </section>
    </div>
  );
};

export default OptimizeMenu;
