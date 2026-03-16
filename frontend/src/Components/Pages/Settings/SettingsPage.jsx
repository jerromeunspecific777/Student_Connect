import React, { useState, useEffect } from "react";
import axios from 'axios';
import "./SettingsPage.css";
import { SiTodoist, SiCanvas } from "react-icons/si";
import { RxNotionLogo } from "react-icons/rx";
import { useNavigate } from 'react-router-dom';
import { encrypt, getCsrfToken } from "../Utils/utils";
import ParticleBackground from "../../Shared/ParticleBackground";

const SettingsPage = ({ setSuccess, setError, publicKey }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [selected, setSelected] = useState("todoist");
  const [linkedStatus, setLinkedStatus] = useState({
    Canvas: false,
    Todoist: false,
    Notion: false
  });

  const navigate = useNavigate();
  const items = [
    { value: "todoist", title: "Todoist", icon: <SiTodoist /> },
    { value: "notion", title: "Notion", icon: <RxNotionLogo /> },
  ];

  const fetchStatus = () => {
    axios.get('https://localhost:5000/api/token-protected', { withCredentials: true })
      .then(response => {
        const data = response.data;
        const value = data.NToken === undefined ? "TToken" : "NToken";
        const api = value === "TToken" ? "todoist" : "notion";
        setSelected(api);

        setLinkedStatus({
          Canvas: data.CToken === "True",
          Todoist: data.TToken === "True",
          Notion: data.NToken === "True"
        });
      })
      .catch(error => {
        setTimeout(() => {
          setError('Please Login To Access The Settings');
          navigate('/login');
        }, 0);
      });
  };

  useEffect(() => {
    fetchStatus();
    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleSaveSettings = async (event) => {
    event.preventDefault();
    try {
      const encryptedSettingsData = {
        api: encrypt(publicKey, selected)
      }
      const csrfToken = getCsrfToken();
      const response = await axios.post(
        "https://localhost:5000/api/settings",
        encryptedSettingsData,
        {
          withCredentials: true,
          headers: {
            "X-CSRF-TOKEN": csrfToken,
          },
        }
      );
      setSuccess(response.data.message)
      navigate('/dashboard')
    } catch (error) {
      if (error.response) {
        setError(error.response.data.error)
        navigate('/dashboard')
      }
    }
  };

  const handleUnlink = async (service) => {
    try {
      const csrfToken = getCsrfToken();
      const response = await axios.post(
        "https://localhost:5000/api/unlink",
        { service },
        {
          withCredentials: true,
          headers: {
            "X-CSRF-TOKEN": csrfToken,
          }
        }
      );
      setSuccess(response.data.message);
      fetchStatus(); // Refresh status after unlinking
    } catch (error) {
      setError(error.response?.data?.error || `Failed to unlink ${service}`);
    }
  };

  return (
    <div className={`auth-container settings-container ${isVisible ? 'in-view' : ''}`}>
      <ParticleBackground />

      <div className='wrapper reveal reveal-up'>
        <h1 className="auth-title">Account Settings</h1>

        <div className="settings-section">
          <div className="section-label">Preferred API:</div>
          <div className="api-selection-grid">
            {items.map((item) => (
              <div
                key={item.value}
                className={`api-card ${selected === item.value ? "selected" : ""}`}
                onClick={() => setSelected(item.value)}
              >
                <div className="api-card-icon">{item.icon}</div>
                <div className="api-card-title">{item.title}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="settings-section integrations-section">
          <div className="section-label">Manage Integrations:</div>
          <div className="integrations-list">
            {/* Canvas Integration */}
            <div className="integration-item">
              <div className="integration-info">
                <div className="integration-icon"><SiCanvas /></div>
                <div>
                  <div className="integration-name">Canvas LMS</div>
                  <div className={`integration-status ${linkedStatus.Canvas ? 'linked' : ''}`}>
                    {linkedStatus.Canvas ? 'Connected' : 'Not Linked'}
                  </div>
                </div>
              </div>
              {linkedStatus.Canvas && (
                <button className="unlink-button" onClick={() => handleUnlink("Canvas")}>Unlink</button>
              )}
            </div>

            {/* Todoist Integration */}
            <div className="integration-item">
              <div className="integration-info">
                <div className="integration-icon"><SiTodoist /></div>
                <div>
                  <div className="integration-name">Todoist</div>
                  <div className={`integration-status ${linkedStatus.Todoist ? 'linked' : ''}`}>
                    {linkedStatus.Todoist ? 'Connected' : 'Not Linked'}
                  </div>
                </div>
              </div>
              {linkedStatus.Todoist && (
                <button className="unlink-button" onClick={() => handleUnlink("Todoist")}>Unlink</button>
              )}
            </div>

            {/* Notion Integration */}
            <div className="integration-item">
              <div className="integration-info">
                <div className="integration-icon"><RxNotionLogo /></div>
                <div>
                  <div className="integration-name">Notion</div>
                  <div className={`integration-status ${linkedStatus.Notion ? 'linked' : ''}`}>
                    {linkedStatus.Notion ? 'Connected' : 'Not Linked'}
                  </div>
                </div>
              </div>
              {linkedStatus.Notion && (
                <button className="unlink-button" onClick={() => handleUnlink("Notion")}>Unlink</button>
              )}
            </div>
          </div>
        </div>

        <button className="auth-button save-settings-btn" onClick={handleSaveSettings}>
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default SettingsPage;
