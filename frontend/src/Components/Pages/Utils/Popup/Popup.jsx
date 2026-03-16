import React, { useEffect } from "react";
import "./Popup.css";
import { FaCheckCircle } from "react-icons/fa";
import { MdOutlineError } from "react-icons/md";

const Popup = ({ message, type = "info", onClose }) => {
    const iconMap = {
        success: <FaCheckCircle className="popup-icon"/>,
        error: <MdOutlineError className="popup-icon"/>
      };  
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`popup ${type}`}>
      {iconMap[type]}
      <span>{message}</span>
    </div>
  );
};

export default Popup;
