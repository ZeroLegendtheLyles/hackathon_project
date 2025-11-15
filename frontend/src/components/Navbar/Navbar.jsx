import { NavLink } from "react-router-dom";
import "./Navbar.css";
import logo from "../../assets/logo.png";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <img src={logo} alt="Logo" className="logo" />
      </div>
      <ul className="nav-links">
        <li>
          <NavLink to="/" className="nav-header">
            Home
          </NavLink>
        </li>
        <li>
          <NavLink to="/menu" className="nav-header">
            Menu
          </NavLink>
        </li>
        <li>
          <NavLink to="/about" className="nav-header">
            About
          </NavLink>
        </li>
        <li>
          <NavLink to="/admin" className="nav-header">
            Admin
          </NavLink>
        </li>
        <li>
          <NavLink to="/metrics" className="nav-header">
            Metrics
          </NavLink>
        </li>
        <li>
          <NavLink to="/trash" className="nav-header">
            Trash of today
          </NavLink>
        </li>
        <li>
          <NavLink to="/optimize-menu" className="nav-header">
            Menu Optimizer
          </NavLink>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
