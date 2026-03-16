import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import axios from 'axios'
import './api/axiosInterceptor';

axios.defaults.baseURL = 'https://localhost:5000'; // Flask backend URL
axios.defaults.withCredentials = true; // Allow sending cookies with requests
createRoot(document.getElementById('root')).render(
   // <StrictMode>
   <App />
   // </StrictMode>,
)
