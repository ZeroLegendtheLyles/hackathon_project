import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import "./Navbar.css";
import logo from "../../assets/logo.png";

const Navbar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);

  const location = useLocation();
  const isDashboardActive =
    toolsOpen ||
    ["/admin", "/metrics", "/trash", "/optimize-menu"].includes(
      location.pathname
    );

  const toggleMobile = () => {
    setMobileOpen((prev) => !prev);
  };

  const closeMobile = () => {
    setMobileOpen(false);
    setToolsOpen(false);
  };

  const toggleTools = () => {
    setToolsOpen((prev) => !prev);
  };

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <div className="navbar-logo">
          <img src={logo} alt="Plate Scope logo" />
        </div>

        <button
          type="button"
          className="nav-toggle"
          aria-label="Toggle navigation"
          onClick={toggleMobile}
        >
          <span />
          <span />
          <span />
        </button>
      </div>

      <ul className={`nav-links ${mobileOpen ? "nav-links--open" : ""}`}>
        <li className="nav-item">
          <NavLink
            to="/"
            onClick={closeMobile}
            className={({ isActive }) =>
              `nav-header ${isActive ? "nav-header--active" : ""}`
            }
          >
            Home
          </NavLink>
        </li>

        <li className="nav-item">
          <NavLink
            to="/menu"
            onClick={closeMobile}
            className={({ isActive }) =>
              `nav-header ${isActive ? "nav-header--active" : ""}`
            }
          >
            Menu
          </NavLink>
        </li>

        <li className="nav-item">
          <NavLink
            to="/about"
            onClick={closeMobile}
            className={({ isActive }) =>
              `nav-header ${isActive ? "nav-header--active" : ""}`
            }
          >
            About
          </NavLink>
        </li>

        <li
          className={`nav-item nav-item--has-dropdown ${
            toolsOpen ? "nav-item--open" : ""
          }`}
        >
          <button
            type="button"
            className={`${
              isDashboardActive
                ? "nav-dropdown-toggle-no-background"
                : "nav-dropdown-toggle"
            }
            nav-header ${isDashboardActive ? "nav-header--active" : ""}`}
            onClick={toggleTools}
          >
            Dashboard
            <span className="nav-dropdown-arrow" />
          </button>

          <ul className="nav-dropdown-menu">
            <li>
              <NavLink
                to="/admin"
                onClick={closeMobile}
                className={({ isActive }) =>
                  `nav-dropdown-link ${
                    isActive ? "nav-dropdown-link--active" : ""
                  }`
                }
              >
                Daily Input
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/metrics"
                onClick={closeMobile}
                className={({ isActive }) =>
                  `nav-dropdown-link ${
                    isActive ? "nav-dropdown-link--active" : ""
                  }`
                }
              >
                Metrics
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/trash"
                onClick={closeMobile}
                className={({ isActive }) =>
                  `nav-dropdown-link ${
                    isActive ? "nav-dropdown-link--active" : ""
                  }`
                }
              >
                Trash of Today
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/optimize-menu"
                onClick={closeMobile}
                className={({ isActive }) =>
                  `nav-dropdown-link ${
                    isActive ? "nav-dropdown-link--active" : ""
                  }`
                }
              >
                Menu Optimizer
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/waste-trend"
                onClick={closeMobile}
                className={({ isActive }) =>
                  `nav-dropdown-link ${
                    isActive ? "nav-dropdown-link--active" : ""
                  }`
                }
              >
                Waste Trend
              </NavLink>
            </li>
          </ul>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
