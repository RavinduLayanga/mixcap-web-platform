import React from "react";
import { Link } from "react-router-dom";
import "./Navbar.css";
import logo from "../../assets/mixcap-logo.png";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <img src={logo} alt="Mixcap Logo" className="navbar-logo-image" />
          <span className="navbar-logo-text">Mixcap</span>
        </Link>

        {/* Left menu */}
        <ul className="navbar-menu">
          <li className="navbar-item">
            <Link to="/" className="navbar-link">Home</Link>
          </li>
          <li className="navbar-item">
            <Link to="/video-caption" className="navbar-link">Video Caption</Link>
          </li>
          <li className="navbar-item">
            <Link to="/about" className="navbar-link">About</Link>
          </li>
          <li className="navbar-item">
            <Link to="/contact" className="navbar-link">Contact</Link>
          </li>
        </ul>

        {/* Right login/register buttons */}
        {/* <div className="navbar-auth">
          <Link to="/login" className="navbar-link login-btn">Login</Link>
          <Link to="/register" className="navbar-link register-btn">Register</Link>
        </div> */}
      </div>
    </nav>
  );
};

export default Navbar;
