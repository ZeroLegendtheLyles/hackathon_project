import React, { useEffect, useState } from "react";
import axios from "axios";
import "./TrashOfToday.css";
import trashcan from "../../assets/trashcan.png";

const API_URL = "http://127.0.0.1:5000";

function getTodayYMD() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

const TrashOfToday = () => {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    const fetchTopDish = async () => {
      try {
        const today = getTodayYMD();
        const res = await axios.get(`${API_URL}/day/${today}/top_dish`);
        setData(res.data);
        setStatus("ok");
      } catch (e) {
        console.log(e);
        setStatus("empty");
      }
    };

    fetchTopDish();
  }, []);

  if (status === "loading") {
    return (
      <div className="trash-today">
        <h3 className="trash-today-title">Trash of the day</h3>
        <p className="trash-today-placeholder">Loading today’s data…</p>
      </div>
    );
  }

  if (status === "empty" || !data || !data.top_dish) {
    return (
      <div className="trash-today">
        <h3 className="trash-today-title">Trash of the day</h3>
        <p className="trash-today-placeholder">
          No data for today yet. Add today’s menu in the admin panel.
        </p>
      </div>
    );
  }

  const dish = data.top_dish;
  const imageSrc = `${API_URL}${dish.image_path}`;

  return (
    <div className="trash-today">
      <h3 className="trash-today-title">Trash of today</h3>

      <div className="dishContainer">
        <div className="trash-today-scene">
          <div className="trash-today-dish-card">
            <div className="trash-today-dish-image-wrap">
              <img
                src={imageSrc}
                alt={dish.dish_name}
                className="trash-today-dish-image"
              />
            </div>
            <div className="trash-today-dish-info">
              <span className="trash-today-dish-name">{dish.dish_name}</span>
              <span className="trash-today-dish-meta">
                {dish.quantity} servings on {data.date}
              </span>
            </div>
          </div>

          <div className="trash-today-bin">
            <img src={trashcan} alt={dish.dish_name} />
          </div>

          <div className="trash-today-floating">
            <img
              src={imageSrc}
              alt={dish.dish_name}
              className="trash-today-floating-img"
            />
          </div>
        </div>

        <p className="trash-today-caption">
          Based on the most served dish today.
        </p>
      </div>
    </div>
  );
};

export default TrashOfToday;
