import React from "react";
import "./Menu.css";

const cards = [
  {
    img: "",
    title: "Breakfast",
  },
  {
    img: "",
    title: "Lunch",
  },
  {
    img: "",
    title: "Dinner",
  },
  {
    img: "",
    title: "Dessert",
  },

];


const Menu = () => {
  return ( 
    <div className="menu">
      <h1 className="menu-title">MENU</h1>

      <section className="menu-content">
        {cards.map((card) => (
          <div key={card.title} className="menu-card">
            <img src={card.img} alt={card.title} />
            <p>{card.title}</p>
          </div>
        ))}
      </section>
    </div>
    );
};

export default Menu;
