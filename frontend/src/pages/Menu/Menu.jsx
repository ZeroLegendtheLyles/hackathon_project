import React, { useEffect, useState } from "react";
import axios from "axios";
import "./Menu.css";

const API_URL = "http://127.0.0.1:5001";

const Menu = () => {
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDishes = async () => {
      try {
        const res = await axios.get(`${API_URL}/dishes_waste_rates`);
        setDishes(res.data.dishes || []);
      } catch (err) {
        setError("Failed to load dishes");
        console.log(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDishes();
  }, []);

  if (loading) {
    return (
      <div className="menu">
        <h2 className="menu-title">Menu</h2>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="menu">
        <h2 className="menu-title">Menu</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="menu">
      <h2 className="menu-title">Menu</h2>

      <section className="menu-content">
        {dishes.map((dish) => (
          <div key={dish.id} className="menu-card">
            <img
              className="menu-card-img"
              src={`${dish.image_path}`}
              alt={dish.name}
            />
            <p className="menu-card-name">Dish {dish.name}</p>
            <p className="menu-card-waste">
              {(dish.waste_rate * 100).toFixed(1)}%
            </p>
          </div>
        ))}
      </section>
    </div>
  );
};

export default Menu;
