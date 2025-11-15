import React, { useEffect, useState } from "react";
import axios from "axios";
import "./Metrics.css";

const API_URL = "http://127.0.0.1:5001";

const Metrics = () => {
  const [summary, setSummary] = useState(null);
  const [topDishes, setTopDishes] = useState([]);
  const [dishOptions, setDishOptions] = useState([]);
  const [selectedDish, setSelectedDish] = useState("");
  const [adjustment, setAdjustment] = useState(80);
  const [impact, setImpact] = useState(null);
  const [impactError, setImpactError] = useState(null);
  const [dateInput, setDateInput] = useState("");
  const [topDishDay, setTopDishDay] = useState(null);
  const [dayError, setDayError] = useState(null);
  const [barsLoaded, setBarsLoaded] = useState(false);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await axios.get(`${API_URL}/days_overview`);
        const days = res.data;
        if (!Array.isArray(days) || days.length === 0) {
          setSummary(null);
          return;
        }

        let totalWaste = 0;
        const dishNames = new Set();

        days.forEach((day) => {
          totalWaste += day.total_waste || 0;
          (day.servings || []).forEach((s) => {
            if (s.dish_name) dishNames.add(s.dish_name);
          });
        });

        const avgDailyWaste = totalWaste / days.length;

        setSummary({
          totalDays: days.length,
          avgDailyWaste,
          totalWaste,
          dishCount: dishNames.size,
        });
      } catch {
        setSummary(null);
      }
    };

    const fetchDishes = async () => {
      try {
        const res = await axios.get(`${API_URL}/dishes_waste_rates`, {
          params: { sort: "desc", order_by: "waste_rate" },
        });
        const dishes = res.data.dishes || [];
        setTopDishes(dishes.slice(0, 3));
        setDishOptions(dishes);
        if (dishes.length > 0) {
          setSelectedDish(dishes[0].name);
        }
        setBarsLoaded(true);
      } catch {
        setTopDishes([]);
        setDishOptions([]);
      }
    };

    const load = async () => {
      await Promise.all([fetchSummary(), fetchDishes()]);
    };

    load();
  }, []);

  const handleImpactSubmit = async (e) => {
    e.preventDefault();
    if (!selectedDish) return;
    setImpactError(null);
    setImpact(null);
    try {
      const res = await axios.post(`${API_URL}/predict_waste_impact`, {
        dish_name: selectedDish,
        adjustment_percentage: Number(adjustment),
      });
      setImpact(res.data);
    } catch (e) {
      const message =
        e.response?.data?.error ||
        "Failed to compute impact. Try another dish.";
      setImpactError(message);
    }
  };

  const handleTopDishDay = async (e) => {
    e.preventDefault();
    if (!dateInput) return;
    setDayError(null);
    setTopDishDay(null);
    try {
      const res = await axios.get(`${API_URL}/day/${dateInput}/top_dish`);
      setTopDishDay(res.data);
    } catch (e) {
      const message =
        e.response?.data?.error || "Could not load top dish for that date.";
      setDayError(message);
    }
  };

  return (
    <div className="metrics">
      <h2 className="metrics-title">Dining Waste Metrics</h2>

      <section className="metrics-grid">
        <div className="metrics-card">
          <h3 className="metrics-card-title">Overview</h3>
          {summary ? (
            <div className="metrics-overview">
              <div className="metrics-overview-item">
                <span className="metrics-overview-label">Days tracked</span>
                <span className="metrics-overview-value">
                  {summary.totalDays}
                </span>
              </div>
              <div className="metrics-overview-item">
                <span className="metrics-overview-label">Avg daily waste</span>
                <span className="metrics-overview-value">
                  {summary.avgDailyWaste.toFixed(2)} kg
                </span>
              </div>
              <div className="metrics-overview-item">
                <span className="metrics-overview-label">Total waste</span>
                <span className="metrics-overview-value">
                  {summary.totalWaste.toFixed(1)} kg
                </span>
              </div>
              <div className="metrics-overview-item">
                <span className="metrics-overview-label">Unique dishes</span>
                <span className="metrics-overview-value">
                  {summary.dishCount}
                </span>
              </div>
            </div>
          ) : (
            <p className="metrics-placeholder">
              No overview available yet. Add some days in the admin panel.
            </p>
          )}
        </div>

        <div className="metrics-card">
          <h3 className="metrics-card-title">Highest waste dishes</h3>
          {topDishes.length > 0 ? (
            <ul className="metrics-list">
              {topDishes.map((dish) => (
                <li key={dish.id} className="metrics-list-item">
                  <div className="metrics-list-main">
                    <span className="metrics-list-name">{dish.name}</span>
                    <span className="metrics-list-rate">
                      {(dish.waste_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="metrics-list-bar">
                    <div
                      className={
                        "metrics-list-bar-fill " +
                        (barsLoaded ? "metrics-list-bar-fill--animate" : "")
                      }
                      style={{
                        "--bar-width": `${(dish.waste_rate * 100).toFixed(1)}%`,
                      }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="metrics-placeholder">No dish waste data yet.</p>
          )}
        </div>
      </section>

      <section className="metrics-grid metrics-grid--two">
        <div className="metrics-card">
          <h3 className="metrics-card-title">Adjustment impact</h3>
          <form className="metrics-form" onSubmit={handleImpactSubmit}>
            <div className="metrics-field">
              <label>Dish</label>
              <select
                value={selectedDish}
                onChange={(e) => setSelectedDish(e.target.value)}
              >
                {dishOptions.map((dish) => (
                  <option key={dish.id} value={dish.name}>
                    {dish.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="metrics-field">
              <label>Serving level</label>
              <input
                type="range"
                min="10"
                max="120"
                step="5"
                value={adjustment}
                onChange={(e) => setAdjustment(e.target.value)}
              />
              <div className="metrics-range-label">
                {adjustment}% of current serving
              </div>
            </div>

            <button type="submit" className="metrics-submit">
              Predict impact
            </button>
          </form>

          {impactError && (
            <p className="metrics-status metrics-status--error">
              {impactError}
            </p>
          )}

          {impact && (
            <div className="metrics-impact">
              <div className="metrics-impact-row">
                <span>Current waste rate</span>
                <span>{(impact.current_waste_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="metrics-impact-row">
                <span>Daily waste change</span>
                <span>
                  {impact.analysis.daily_average_changes.daily_waste_reduction.toFixed(
                    2
                  )}{" "}
                  kg
                </span>
              </div>
              <div className="metrics-impact-row">
                <span>Daily rate change</span>
                <span>
                  {(
                    impact.analysis.daily_average_changes
                      .daily_waste_rate_reduction * 100
                  ).toFixed(2)}
                  %
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="metrics-card">
          <h3 className="metrics-card-title">Top dish by day</h3>
          <form className="metrics-form" onSubmit={handleTopDishDay}>
            <div className="metrics-field">
              <label>Date</label>
              <input
                type="date"
                value={dateInput}
                onChange={(e) => setDateInput(e.target.value)}
              />
            </div>
            <button type="submit" className="metrics-submit">
              Load top dish
            </button>
          </form>

          {dayError && (
            <p className="metrics-status metrics-status--error">{dayError}</p>
          )}

          {topDishDay && (
            <div className="metrics-top-dish-card">
              <div className="metrics-top-dish-header">
                <span className="metrics-top-dish-date">{topDishDay.date}</span>
              </div>
              <div className="metrics-top-dish-main">
                <span className="metrics-top-dish-name">
                  {topDishDay.top_dish.dish_name}
                </span>
                <span
                  className="metrics-top-dish-qty"
                  style={{ color: "#ffd166" }}
                >
                  {topDishDay.top_dish.quantity} servings
                </span>
              </div>
              <div className="metrics-top-dish-meta">
                <span>{topDishDay.total_dishes} dishes that day</span>
                <span>{topDishDay.total_serving} total servings</span>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Metrics;
