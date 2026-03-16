import React, { useState, useEffect } from 'react'
import './LoginPage.css'
import { FaEnvelope } from "react-icons/fa"
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios'
import { encrypt } from '../Utils/utils';
import ParticleBackground from '../../Shared/ParticleBackground'

const LoginPage = ({ setSuccess, setError, isLogged, setLogged, publicKey }) => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);

  // Step 1: Email, Step 2: OTP
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(new Array(6).fill(""));
  const [timezone, setTimezone] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  if (isLogged) {
    return navigate('/dashboard')
  }

  useEffect(() => {
    const timezoneOptions = Intl.DateTimeFormat().resolvedOptions();
    setTimezone(timezoneOptions.timeZone);

    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleEmailChange = (event) => {
    setEmail(event.target.value);
  };

  const handleRememberMeChange = (event) => {
    setRememberMe(event.target.checked);
  };

  const handleOtpChange = (element, index) => {
    if (isNaN(element.value)) return false;

    const newOtp = [...otp];
    newOtp[index] = element.value;
    setOtp(newOtp);

    // Focus next input automatically
    if (element.value && element.nextSibling) {
      element.nextSibling.focus();
    }
  };

  const handleKeyDown = (e, index) => {
    if (e.key === "Backspace") {
      if (!otp[index] && e.target.previousSibling) {
        e.target.previousSibling.focus();
      }
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").slice(0, 6).split("");
    if (pastedData.every(char => !isNaN(char))) {
      const newOtp = [...otp];
      pastedData.forEach((val, i) => {
        if (i < 6) newOtp[i] = val;
      });
      setOtp(newOtp);
    }
  };

  const maskEmail = (emailStr) => {
    if (!emailStr.includes('@')) return emailStr;
    const [name, domain] = emailStr.split('@');
    if (!name) return emailStr;
    return `${name[0]}******@${domain}`;
  };

  const resetToEmail = () => {
    setOtp(new Array(6).fill(""));
    setStep(1);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (step === 1) {
      // Step 1: Submit Email to get Code (/api/code)
      try {
        const encryptedEmailData = {
          email: encrypt(publicKey, email)
        }

        // Post to /api/code
        const response = await axios.post('https://localhost:5000/api/code', encryptedEmailData, { withCredentials: true });

        setSuccess(response.data.message || "Code sent to your email!");
        setStep(2); // Move to OTP step on success
      } catch (error) {
        if (error.response) {
          setError(error.response.data.error)
        } else {
          setError("An error occurred. Please try again.")
        }
      }
    } else {
      // Step 2: Verify Code (/api/login)
      const otpCode = otp.join("");
      if (otpCode.length !== 6) {
        setError("Please enter the full 6-digit code.");
        return;
      }

      try {
        const encryptedLoginData = {
          email: encrypt(publicKey, email),
          code: encrypt(publicKey, otpCode),
          timezone: encrypt(publicKey, timezone),
          rememberMe: rememberMe
        }

        // Post to /api/login to verify code and login
        const response = await axios.post('https://localhost:5000/api/login', encryptedLoginData, { withCredentials: true });

        setSuccess(response.data.message || "Login successful!");
        setLogged(true)
        navigate('/dashboard')
      } catch (error) {
        if (error.response) {
          setError(error.response.data.error)
          if (error.response.status === 403) {
            resetToEmail();
            setEmail('');
          }
        } else {
          setError("An error occurred. Please try again.")
        }
      }
    }
  };

  return (
    <div className={`auth-container ${isVisible ? 'in-view' : ''}`}>
      <ParticleBackground />

      <div className='wrapper reveal reveal-up'>
        <form onSubmit={handleSubmit}>
          <h1 className="auth-title">{step === 1 ? 'Login' : 'Enter Code'}</h1>

          {step === 1 ? (
            <>
              <div className='input-box'>
                <input
                  type="text"
                  placeholder='Email'
                  name='email'
                  value={email}
                  onChange={handleEmailChange}
                  required
                />
                <FaEnvelope className='iconE' />
              </div>
              <div className="remember-forgot">
                <label className="checkbox-container">
                  <input type='checkbox' checked={rememberMe} onChange={handleRememberMeChange} />
                  <div className="checkbox-inner">
                    <svg viewBox="0 0 64 64">
                      <path d="M 0 16 V 56 A 8 8 90 0 0 8 64 H 56 A 8 8 90 0 0 64 56 V 8 A 8 8 90 0 0 56 0 H 8 A 8 8 90 0 0 0 8 V 16 L 32 48 L 64 16 V 8 A 8 8 90 0 0 56 0 H 8 A 8 8 90 0 0 0 8 V 56 A 8 8 90 0 0 8 64 H 56 A 8 8 90 0 0 64 56 V 16" pathLength="575.0541381835938" className="path" />
                    </svg>
                  </div>
                  <span>Remember Me</span>
                </label>
              </div>
              <button type='submit' className="auth-button">Login</button>
            </>
          ) : (
            <>
              <p className="auth-subtitle">
                Enter the 6-digit code sent to <br />
                <strong>{maskEmail(email)}</strong>
              </p>

              <div className="otp-input-container" onPaste={handlePaste}>
                {otp.map((data, index) => {
                  return (
                    <input
                      className="otp-field"
                      type="text"
                      name="otp"
                      maxLength="1"
                      key={index}
                      value={data}
                      onChange={e => handleOtpChange(e.target, index)}
                      onKeyDown={e => handleKeyDown(e, index)}
                      onFocus={e => e.target.select()}
                    />
                  );
                })}
              </div>

              <button type='submit' className="auth-button">Verify</button>
              <div className="register-link">
                <p><a onClick={resetToEmail} style={{ cursor: 'pointer' }}>Back to Email</a></p>
              </div>
            </>
          )}

          <div className="register-link">
            <p>Don't have an account? <Link to="/register">Register</Link></p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default LoginPage