import React, { useEffect, useState } from 'react'
import './Navbar.css'
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { getCsrfToken } from '../Utils/utils';
import { IoMenu, IoClose } from "react-icons/io5";
import axios from 'axios';

const Navbar = ({ isLogged, setIsLogged, setSuccess, setError, publicKey, setPublicKey }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  // Close menu when route changes
  useEffect(() => {
    setIsMenuOpen(false)
  }, [location]);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen)
  useEffect(() => {
    if (!publicKey) {
      const fetchPublicKey = async () => {
        try {
          const response = await axios.get('https://localhost:5000/api/public-key');
          setPublicKey(response.data);
        } catch (error) {
          console.error('Error fetching public key:', error);
        }
      };
      fetchPublicKey();
    };
  }, []);
  const handleLogout = async (event) => {
    event.preventDefault();
    try {
      const csrfToken = getCsrfToken()
      const response = await axios.get('https://localhost:5000/api/logout', {
        withCredentials: true, headers: {
          'X-CSRF-TOKEN': csrfToken,
        }
      });
      setTimeout(() => {
        setIsLogged(false);
        setSuccess(response.data.message);
        navigate('/');
      }, 0);
    } catch (error) {
      if (error.response) {
        setError(error.response.data.error)
      }
    }
  };
  return (
    <header className="header">
      <Link to="/" className="logo">Student Connect</Link>

      <button className="menu-toggle" onClick={toggleMenu} aria-label="Toggle Navigation">
        {isMenuOpen ? <IoClose /> : <IoMenu />}
      </button>

      <nav className={`navbar ${isMenuOpen ? 'active' : ''}`}>
        <Link to="/" onClick={() => setIsMenuOpen(false)}>Home</Link>
        <Link to="/dashboard" onClick={() => setIsMenuOpen(false)}>Dashboard</Link>
        {!isLogged ? (
          <Link to="/register" onClick={() => setIsMenuOpen(false)}>Register</Link>
        ) : (
          <Link to="/settings" onClick={() => setIsMenuOpen(false)}>Settings</Link>
        )}
        {!isLogged ? (
          <Link to="/login" onClick={() => setIsMenuOpen(false)}>Login</Link>
        ) : (
          <Link onClick={(e) => { handleLogout(e); setIsMenuOpen(false); }}>Logout</Link>
        )}
      </nav>

      {/* Mobile Backdrop */}
      {isMenuOpen && <div className="menu-backdrop" onClick={() => setIsMenuOpen(false)}></div>}
    </header>
  )
}

export default Navbar