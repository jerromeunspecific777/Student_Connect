import React, { useState, useEffect } from "react";
import "./DialogS.css";
import { FaCheckCircle, FaPlusCircle, FaEdit } from "react-icons/fa";

const DialogS = ({ isOpen, onClose, api, added, updated }) => {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => setShowContent(true), 100);
      return () => clearTimeout(timer);
    } else {
      setShowContent(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className={`dialog-overlayS ${showContent ? 'active' : ''}`} onClick={onClose}>
      <div
        className={`dialog-contentS ${showContent ? 'active' : ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="dialog-headerS">
          <FaCheckCircle className="success-icon" />
          <h2 className="dialog-titleS">Process Complete</h2>
          <p className="dialog-subtitleS">Canvas + {api}</p>
        </div>

        <div className="dialog-bodyS">
          <div className="stats-container">
            <div className="stat-item reveal-up">
              <FaPlusCircle className="stat-icon added" />
              <div className="stat-info">
                <span className="stat-value">{added}</span>
                <span className="stat-label">Added</span>
              </div>
            </div>

            <div className="stat-item reveal-up" style={{ animationDelay: '0.1s' }}>
              <FaEdit className="stat-icon updated" />
              <div className="stat-info">
                <span className="stat-value">{updated}</span>
                <span className="stat-label">Updated</span>
              </div>
            </div>
          </div>

          <p className="footerS">Your tasks are now ready to view.</p>
        </div>

        <button className="dialog-save-btnS" onClick={onClose}>
          Got it
        </button>
      </div>
    </div>
  );
};

export default DialogS;
