import React from "react";
import "./Hero.css";

const Hero = () => {
  return (
    <div className="hero">
      <section className="hero-text">
        <h1 className="hero-subtitle">Haverford</h1>
        <h1 className="hero-title">Our Name</h1>
        <p className="hero-intro">Dining Waste</p>
      </section>

      <section className="hero-image">
          <img 
            className="hero-image"
            src=""
          />
        <div className="hero-shadow"/>
      </section>
    </div>
  );
};

export default Hero;
