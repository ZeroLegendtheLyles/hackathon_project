import { NavLink } from "react-router-dom";
import "./Navbar.css";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <img src="" alt="Logo" />
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
          <NavLink to="/shop" className="nav-header">
            Shop
          </NavLink>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
