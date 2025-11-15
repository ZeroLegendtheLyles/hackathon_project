import React from "react";
import "./Hero.css";
import hero from "../../assets/hero.png";

const Hero = () => {
  return (
    <div className="hero">
      <section className="hero-text">
        <h2 className="hero-subtitle">Haverford</h2>
        <h1 className="hero-title">Plate Scope</h1>
        <p className="hero-intro">Know Your Dining Waste</p>
      </section>

      <section className="hero-image">
        <img className="hero-image" src={hero} />
        <div className="hero-shadow" />
      </section>
    </div>
  );
};

export default Hero;
