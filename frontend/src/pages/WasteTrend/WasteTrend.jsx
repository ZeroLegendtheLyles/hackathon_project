import React, { useState } from "react";
import axios from "axios";
import "./WasteTrend.css";

const API_URL = "http://127.0.0.1:5001";

const WasteTrend = () => {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [chartData, setChartData] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus(null);
    setChartData(null);

    if (!startDate || !endDate) {
      setStatus({
        type: "error",
        message: "Please select both start and end dates.",
      });
      return;
    }

    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/waste_trend_chart`, {
        start_date: startDate,
        end_date: endDate,
      });

      if (res.data && res.data.success && res.data.chart_data) {
        setChartData(res.data.chart_data);
        setStatus(null);
      } else {
        setStatus({
          type: "error",
          message: "Could not generate chart. Please try again.",
        });
      }
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        "Failed to generate chart. Check the dates.";
      setStatus({ type: "error", message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="waste-trend">
      <h2 className="waste-trend-title">Waste Trend</h2>

      <div className="waste-trend-form-container">
        <form className="waste-trend-form" onSubmit={handleSubmit}>
          <div className="waste-trend-fields">
            <div className="waste-field">
              <label htmlFor="start-date">Start date</label>
              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="waste-field">
              <label htmlFor="end-date">End date</label>
              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            className="waste-trend-submit"
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate trend"}
          </button>

          {status && (
            <p
              className={`waste-status ${
                status.type === "success"
                  ? "waste-status--success"
                  : "waste-status--error"
              }`}
            >
              {status.message}
            </p>
          )}
        </form>
      </div>

      {chartData && chartData.image_base64 && (
        <div className="waste-trend-chart-wrapper">
          <div className="waste-trend-chart-card">
            <h3 className="waste-trend-chart-title">
              Waste rate trend ({chartData.date_range})
            </h3>
            <img
              className="waste-trend-chart-image"
              src={`data:image/png;base64,${chartData.image_base64}`}
              alt="Waste rate trend chart"
            />
            <p className="waste-trend-chart-meta">
              Days: {chartData.total_days}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default WasteTrend;
