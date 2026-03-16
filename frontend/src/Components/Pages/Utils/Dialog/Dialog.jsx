import React from "react";
import "./Dialog.css";
import { Link } from 'react-router-dom';

const Dialog = ({ isOpen, onClose, email, setEmail,  ChangePass}) => {
  if (!isOpen) return null;

  const handleOverlayClick = (event) => {
    if (event.target.classList.contains("dialog-overlay")) {
      onClose();
    }
  };

  const handleInputChange = (event) => {
    const { value } = event.target;
    setEmail(value);
  };

  return (
    <div className="dialog-overlay" onClick={handleOverlayClick}>
      <div className="dialog-content">
        <button className="dialog-close" onClick={onClose}>
          &times;
        </button>
        <div className="dialog-header">
          <h2 className="dialog-title">Forgot Password</h2>
        </div>
        <div className="dialog-body">
          <p>Email:</p>
          <input
            type="text"
            placeholder="Enter your email"
            value={email}
            onChange={handleInputChange}
            required
          />
        </div>
        <button className="dialog-save-btn" onClick={ChangePass}>Send Email</button>
        <span className="registerText">
          Don't have an account?{" "}
          <Link to="/register" onClick={onClose}>
            Register
          </Link>
        </span>
      </div>
    </div>
  );
};

export default Dialog;
