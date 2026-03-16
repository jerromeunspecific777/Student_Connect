import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { LoadingBarProvider } from './Components/Pages/Utils/LoadingBar';
import LoginPage from './Components/Pages/Login/LoginPage'
import Navbar from './Components/Pages/Navbar/Navbar'
import RegisterPage from './Components/Pages/Register/RegisterPage';
import StartPage from './Components/Pages/Start/StartPage';
import PopupContainer from './Components/Pages/Utils/Popup/PopupContainer';
import Dashboard from './Components/Pages/Dashboard/Dashboard';
import CanvasLink from './Components/Pages/Dashboard/Canvas/CanvasLink';
import SettingsPage from './Components/Pages/Settings/SettingsPage';

import axios from 'axios';

function App() {
  const [publicKey, setPublicKey] = useState('');
  const [popups, setPopups] = useState([]);
  const [isLogged, setIsLogged] = useState(false);

  const addPopup = useCallback((message, type) => {
    const id = Date.now();
    setPopups((prevPopups) => [...prevPopups, { id, message, type }]);
  }, []);

  const removePopup = useCallback((id) => {
    setPopups((prevPopups) => prevPopups.filter((popup) => popup.id !== id));
  }, []);

  useEffect(() => {
    const checkToken = async () => {
      try {
        // We always try to hitting the protected route. 
        // If the access token is missing/expired, the interceptor will try refreshing.
        await axios.get("/api/token-protected");
        setIsLogged(true);
      } catch (error) {
        setIsLogged(false);
      }
    };

    checkToken();
  }, []);

  return (
    <LoadingBarProvider>
      <Router>
        <PopupContainer popups={popups} removePopup={removePopup} />
        <Navbar isLogged={isLogged} setIsLogged={setIsLogged} setSuccess={(msg) => addPopup(msg, "success")} setError={(msg) => addPopup(msg, "error")} publicKey={publicKey} setPublicKey={setPublicKey} />
        <Routes>
          <Route path="/" element={<StartPage />} />
          <Route path="/login" element={<LoginPage setSuccess={(msg) => addPopup(msg, "success")} setError={(msg) => addPopup(msg, "error")} isLogged={isLogged} setLogged={setIsLogged} publicKey={publicKey} />} />
          <Route path="/register" element={<RegisterPage setSuccess={(msg) => addPopup(msg, "success")} setError={(msg) => addPopup(msg, "error")} publicKey={publicKey} />} />
          <Route path="/dashboard" element={<Dashboard setSuccess={(msg) => addPopup(msg, "success")} setError={(msg) => addPopup(msg, "error")} publicKey={publicKey} />} />
          <Route path='/canvas' element={<CanvasLink setSuccess={(msg) => addPopup(msg, "success")} setError={(msg) => addPopup(msg, "error")} publicKey={publicKey} />} />
          <Route path='/settings' element={<SettingsPage setSuccess={(msg) => addPopup(msg, "success")} setError={(msg) => addPopup(msg, "error")} publicKey={publicKey} />} />

        </Routes>
      </Router>
    </LoadingBarProvider>
  )
}

export default App
