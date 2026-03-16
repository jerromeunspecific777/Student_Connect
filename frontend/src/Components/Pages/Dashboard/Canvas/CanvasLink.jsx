import React, { useState, useEffect } from "react";
import axios from "axios";
import "./CanvasLink.css";
import { SiCanvas } from "react-icons/si";
import { useNavigate } from "react-router-dom";
import { encrypt, getCsrfToken } from "../../Utils/utils";
import ParticleBackground from "../../../Shared/ParticleBackground";

const CanvasLink = ({ setSuccess, setError, publicKey }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [canvasAPI, setCanvasAPI] = useState("");
  const [IsDisabled, setIsDisabled] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [selectedValue, setSelectedValue] = useState("Select Your University");
  const navigate = useNavigate();

  useEffect(() => {
    axios
      .get("https://localhost:5000/api/token-protected", {
        withCredentials: true,
      })
      .then((response) => {
        const data = response.data;
        if (data.CToken == "True") {
          setIsDisabled(true);
          setError("Already Linked Canvas");
          // setError("To Unlink Go To Settings"); // Optional: Keep or remove based on preference
          navigate("/dashboard");
        } else if (data.CToken == "False") {
          setIsDisabled(false);
        }
      })
      .catch((error) => {
        console.log(error);
        setError("Please Login To Access The Dashboard");
        navigate("/login");
      });

    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []); // Empty dependency array ensures it only runs on mount

  const handleInputChangeCanvas = (event) => {
    const { value } = event.target;
    setCanvasAPI(value);
  };

  const toggleDropdown = () => {
    setIsActive(!isActive);
  };

  const handleSelect = (value) => {
    setSelectedValue(value);
    setIsActive(false);
  };

  const handleSubmitCanvas = async (event) => {
    event.preventDefault();
    if (selectedValue == "Select Your University") {
      return setError("Please Select An University")
    }
    try {
      const encryptedCanvasToken = {
        University: selectedValue,
        CToken: encrypt(publicKey, canvasAPI),
      };
      const csrfToken = getCsrfToken();
      const response = await axios.post(
        "https://localhost:5000/api/canvas-api-link",
        encryptedCanvasToken,
        {
          withCredentials: true,
          headers: {
            "X-CSRF-TOKEN": csrfToken,
          },
        }
      );
      setCanvasAPI("");
      setSelectedValue("Select Your University");
      setSuccess(response.data.message);
      navigate("/dashboard");
    } catch (error) {
      if (error.response) {
        setCanvasAPI("");
        setSelectedValue("Select Your University");
        setError(error.response.data.error);
      }
    }
  };

  return (
    <div className={`auth-container ${isVisible ? 'in-view' : ''}`}>
      <ParticleBackground />

      <div className='wrapper reveal reveal-up'>
        <form onSubmit={handleSubmitCanvas}>
          <h1 className="auth-title">Canvas Link</h1>

          <div className='input-box'>
            <input
              type="password"
              placeholder='API Token'
              name='canvas-token'
              value={canvasAPI}
              onChange={handleInputChangeCanvas}
              disabled={IsDisabled}
              required
            />
            <SiCanvas className='icon' />
          </div>

          <div className="register-link" style={{ marginTop: '-15px', marginBottom: '15px' }}>
            <p>
              <a
                href="https://community.canvaslms.com/t5/Canvas-Basics-Guide/How-do-I-manage-API-access-tokens-in-my-user-account/ta-p/615312"
                target="_blank"
                rel="noreferrer"
                className="help-link"
              >
                How To Get Token?
              </a>
            </p>
          </div>

          <div className="dropdown-root">
            <div className={`theme-dropdown ${isActive ? "active" : ""}`} onClick={toggleDropdown}>
              <div className="theme-select">
                <span>{selectedValue}</span>
                <i className={`fa fa-chevron-down ${isActive ? "rotate" : ""}`}></i>
              </div>
              <ul className="theme-dropdown-menu">
                <li onClick={() => handleSelect("USF")}>USF</li>
                <li onClick={() => handleSelect("UF")}>UF</li>
                <li onClick={() => handleSelect("UCF")}>UCF</li>
                <li onClick={() => handleSelect("FSU")}>FSU</li>
              </ul>
            </div>
          </div>

          <button
            type="submit"
            className="auth-button"
            style={{ marginTop: '24px' }}
            disabled={IsDisabled}
            title={IsDisabled ? "Already Linked" : ""}
          >
            Link Canvas
          </button>
        </form>
      </div>
    </div>
  );
};

export default CanvasLink;
