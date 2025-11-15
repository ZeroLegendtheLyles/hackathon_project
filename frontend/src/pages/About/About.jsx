import React from "react";
import "./About.css";

const About = () => {
  return (
    <div>
      <img classname="about-img"/>

      <h2 className="about-title">About Us</h2>

      <div className="about-section1">
        <h3 className="about-subtitle">Our Mission</h3>
        <p className="about-description">
        At PlateScope, we are committed to reducing food waste one meal at a time through the power of data. Our goal is to drive sustainable practices in food service, minimize waste, and cultivate a more responsible dining culture in cafeterias worldwide.
        </p>
      </div>

      <img classname="about-img"/>

      <div className="about-section2">
        <h3 className="about-subtitle">What We Do</h3>
        <p className="about-description">
        Our platform provides a comprehensive tracking and analytics solution for food consumption and waste in cafeteria settings. We are dedicated to:
        </p>
        <h4 className="about-point-title">Counting Meals:</h4>
        <p className="about-point-description">
        Precisely tracking preparation and serving quantities for each dish.
        </p>
        <h4 className="about-point-title">Monitoring Waste:</h4>
        <p className="about-point-description">
        Recording leftover food volumes through user-friendly tools.
        </p>
        <h4 className="about-point-title">Analyzing Trends:</h4>
        <p className="about-point-description">
        Identifying most and least wasted foods via clear data visualizations and detailed reports.
        </p>
        <h4 className="about-point-title">Empowering Data-Driven Decisions:</h4>
        <p className="about-point-description">
        Helping cafeteria managers, nutritionists, and sustainability officers optimize menu planning, portion control, and procurement strategies.
        </p>
      </div>

      <img classname="about-img"/>

      <div className="about-section2">
        <h3 className="about-subtitle">Why It Matters</h3>
        <p className="about-description">
        Food waste is more than an operational issue—it's an environmental, social, and economic challenge. By understanding what food is wasted, we can:        </p>
        <h4 className="about-point-title">Reduce environmental impact:</h4>
        <p className="about-point-description">
        Minimize carbon footprints associated with food production and waste disposal.
        </p>
        <h4 className="about-point-title">Save operational costs:</h4>
        <p className="about-point-description">
        Cut unnecessary food procurement and waste disposal expenses.
        </p>
        <h4 className="about-point-title">Support sustainability goals:</h4>
        <p className="about-point-description">
        Contribute to local and global initiatives building a greener planet.
        </p>
      </div>

      <img classname="about-img"/>

      <div className="about-section2">
        <h3 className="about-subtitle">Join Us in Making a Difference</h3>
        <p className="about-description">
        Whether you're a cafeteria manager, sustainability advocate, or part of a food service team, you can be part of the solution. Explore our tools, discover data insights, and join us in building a more efficient and responsible food system.
        </p>
      </div>
    </div>
  );
};

export default About;
