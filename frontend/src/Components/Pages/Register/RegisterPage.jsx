import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './RegisterPage.css'
import { FaUser, FaEnvelope } from "react-icons/fa"
import { Link, useNavigate } from 'react-router-dom';
import { encrypt, validateEmail } from '../Utils/utils';
import ParticleBackground from '../../Shared/ParticleBackground'

const RegisterPage = ({ setSuccess, setError, publicKey }) => {
  const [registerData, setRegisterData] = useState({
    name: '',
    email: '',
  });
  const [isChecked, setIsChecked] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleCheckboxChange = () => {
    setIsChecked(!isChecked);
  };

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setRegisterData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isChecked == false) {
      return setError('Check the Checkbox')
    }
    try {
      if (!validateEmail(registerData.email)) {
        setRegisterData({
          name: '',
          email: '',
        });
        setIsChecked(false)
        return setError('Invalid Email')
      }

      const encryptedRegisterData = {
        name: encrypt(publicKey, registerData.name),
        email: encrypt(publicKey, registerData.email),
      }

      await axios.post('https://localhost:5000/api/register', encryptedRegisterData);

      setRegisterData({
        name: '',
        email: '',
      });
      setIsChecked(false)
      setSuccess("Successfully Registered Your Account")
      navigate('/login')
    } catch (error) {
      if (error.response) {
        setRegisterData({
          name: '',
          email: '',
        });
        setIsChecked(false)
        setError(error.response.data.error)
      }
    }
  };

  return (
    <div className={`auth-container ${isVisible ? 'in-view' : ''}`}>
      <ParticleBackground />

      <div className='wrapper reveal reveal-up'>
        <form onSubmit={handleSubmit}>
          <h1 className="auth-title">Registration</h1>

          <div className='input-box'>
            <input type="text" placeholder='Name' name='name' value={registerData.name} onChange={handleInputChange} required />
            <FaUser className='icon' />
          </div>

          <div className='input-box'>
            <input type="text" placeholder='Email' name='email' value={registerData.email} onChange={handleInputChange} required />
            <FaEnvelope className='icon' />
          </div>

          <label className="container">
            <input type="checkbox" checked={isChecked} onChange={handleCheckboxChange} />
            <svg viewBox="0 0 64 64" height="1em" width="1em">
              <path d="M 0 16 V 56 A 8 8 90 0 0 8 64 H 56 A 8 8 90 0 0 64 56 V 8 A 8 8 90 0 0 56 0 H 8 A 8 8 90 0 0 0 8 V 16 L 32 48 L 64 16 V 8 A 8 8 90 0 0 56 0 H 8 A 8 8 90 0 0 0 8 V 56 A 8 8 90 0 0 8 64 H 56 A 8 8 90 0 0 64 56 V 16" pathLength="575.0541381835938" className="path" />
            </svg>
            <span className="terms-text">I agree to the terms & conditions</span>
          </label>

          <button type='submit' className="auth-button">Register</button>

          <div className="login-link">
            <p>Already have an account? <Link to="/login">Login</Link></p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default RegisterPage