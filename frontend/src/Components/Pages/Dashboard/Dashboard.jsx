import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLoadingBar } from '../Utils/LoadingBar';
import axios from 'axios';
import './Dashboard.css'
import { RxNotionLogo } from "react-icons/rx";
import { SiCanvas, SiTodoist } from "react-icons/si";
import { FaSync } from "react-icons/fa";
import { IoMdTime } from "react-icons/io";
import { loadNewTime, getAverageTime, getCsrfToken } from '../Utils/utils';
import DialogS from '../Utils/Dialog/DialogS';
import ParticleBackground from '../../Shared/ParticleBackground';
import RecentActivity from './RecentActivity';

const Dashboard = ({ setSuccess, setError, publicKey }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [IsDisabledC, setIsDisabledC] = useState(true)
  const [IsDisabledN, setIsDisabledN] = useState(true)
  const [IsDisabledT, setIsDisabledT] = useState(true)
  const [IsDisabledS, setIsDisabledS] = useState(true)
  const [whichAPI, setwhichAPI] = useState(true) // if true use todolit, if false use notion
  const [userName, setuserName] = useState("")
  const [apiSelect, setapiSelect] = useState("")
  const { startLoading, stopLoading } = useLoadingBar()
  const [syncResults, setSyncResults] = useState({ api: "", added: 0, updated: 0 });
  const [syncHistory, setSyncHistory] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [autoSync, setAutoSync] = useState(false);
  const [syncInterval, setSyncInterval] = useState(24);
  const navigate = useNavigate();

  const fetchSyncHistory = () => {
    axios.get('https://localhost:5000/api/sync-history', { withCredentials: true })
      .then(response => {
        setSyncHistory(response.data);
      })
      .catch(error => {
        console.error("Error fetching sync history:", error);
      });
  };

  useEffect(() => {
    let timer;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown(prev => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  useEffect(() => {
    fetchSyncHistory();
    // Make the GET request when the component mounts
    axios.get('https://localhost:5000/api/token-protected', { withCredentials: true })
      .then(response => {
        const data = response.data;
        const value = data.NToken === undefined ? "TToken" : "NToken";
        const account = value === "TToken" ? "Todoist" : "Notion";
        setapiSelect(account)
        setuserName(data.User)
        if (data.CToken == 'True') {
          setIsDisabledC(true)
        } else if (data.CToken == 'False') {
          setIsDisabledC(false)
        }
        if (value == 'TToken') {
          setwhichAPI(true)
          if (data[value] == 'True') {
            setIsDisabledT(true)
          } else {
            setIsDisabledT(false)
          }
        } else if (value == 'NToken') {
          setwhichAPI(false)
          if (data[value] == 'True') {
            setIsDisabledN(true)
          } else {
            setIsDisabledN(false)
          }
        }
        setIsDisabledS(false)

        // Handle URL status tokens
        const params = new URLSearchParams(window.location.search);
        const messageParam = params.get('status');
        if (messageParam === "200") {
          setSuccess(`Successfully Linked ${account} Account`);
          // Clear URL parameter so it doesn't trigger again
          navigate('/dashboard', { replace: true });
        } else if (messageParam === "400") {
          setError(`Unable to Link ${account} Account`);
          navigate('/dashboard', { replace: true });
        } else if (messageParam === "101") {
          setError("Please Use The Notion Template Provided");
          navigate('/dashboard', { replace: true });
        }
      })
      .catch(error => {
        setTimeout(() => {
          setError('Please Login To Access The Dashboard');
          navigate('/login');
        }, 0);
      });

    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, [navigate]); // Only trigger on mount/navigation

  // Fetch auto-sync schedule on mount
  useEffect(() => {
    axios.get('https://localhost:5000/api/schedule', { withCredentials: true })
      .then(response => {
        const data = response.data;
        setAutoSync(data.auto_sync || false);
        setSyncInterval(data.sync_interval || 4);
      })
      .catch(() => { });
  }, []);

  const handleCanvasButton = () => {
    navigate('/canvas')
  };

  const handleLinkTodoist = () => {
    const state = btoa(Math.random().toString()).substring(0, 16);
    document.cookie = `oauth_state=${state}; path=/; secure; samesite=None`;
    const clientId = '8f95e5bfa5c042b384a08727c2d2deac';
    window.location.href = `https://todoist.com/oauth/authorize?client_id=${clientId}&scope=data:read_write,data:delete&state=${state}`;
  };

  const handleLinkNotion = () => {
    const state = btoa(Math.random().toString()).substring(0, 16);
    document.cookie = `oauth_state=${state}; path=/; secure; samesite=None`;
    const clientId = '12bd872b-594c-8048-898a-0037a1911aed';
    const redirectUri = encodeURIComponent('https://localhost:5000/api/notion-api-link');
    window.location.href = `https://api.notion.com/v1/oauth/authorize?owner=user&client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&state=${state}`;
  };

  const handleSync = async (event) => {
    event.preventDefault();
    if (!IsDisabledC) return setError("Please Link Canvas")
    if (apiSelect === "Todoist" && !IsDisabledT) return setError("Please Link Todoist")
    if (apiSelect === "Notion" && !IsDisabledN) return setError("Please Link Notion")

    setIsDisabledS(true)
    const whichTable = apiSelect.charAt(0)
    const tableData = localStorage.getItem(`tableTime${whichTable}`)
    const avgTime = getAverageTime(tableData || "[]")
    const startTime = Date.now();

    try {
      startLoading(avgTime);
      const response = await axios.get('https://localhost:5000/api/sync', { withCredentials: true });

      setSyncResults({
        api: apiSelect,
        added: response.data.Added,
        updated: response.data.Updated
      });

      stopLoading();
      setIsDialogOpen(true);
      const duration = Date.now() - startTime;
      localStorage.setItem(`tableTime${whichTable}`, loadNewTime(duration, tableData || "[]"))
      setSuccess(`Successfully Synced Canvas & ${apiSelect}`)
      fetchSyncHistory(); // Refresh activity log
    } catch (error) {
      if (error.response && error.response.status === 429) {
        setCooldown(error.response.data.remaining || 60);
        setError(error.response.data.message || "Sync is cooling down");
      } else {
        setError("There was an issue syncing");
      }
      stopLoading(true);
    }
    setIsDisabledS(false)
  };

  const handleAutoSyncToggle = async () => {
    const newState = !autoSync;
    setAutoSync(newState);
    try {
      const csrfToken = getCsrfToken();
      await axios.post('https://localhost:5000/api/schedule', {
        enabled: newState,
        interval: newState ? syncInterval : null
      }, {
        withCredentials: true,
        headers: { 'X-CSRF-TOKEN': csrfToken }
      });
      if (newState) {
        const label = { 24: '1 day', 72: '3 days', 168: '1 week' }[syncInterval];
        setSuccess(`Auto-sync enabled every ${label}`);
      } else {
        setSuccess('Auto-sync disabled');
      }
    } catch (error) {
      setAutoSync(!newState); // Revert on failure
      setError('Failed to update auto-sync setting');
    }
  };

  const handleIntervalChange = async (newInterval) => {
    setSyncInterval(newInterval);
    if (autoSync) {
      try {
        const csrfToken = getCsrfToken();
        await axios.post('https://localhost:5000/api/schedule', {
          enabled: true,
          interval: newInterval
        }, {
          withCredentials: true,
          headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        const label = { 24: '1 day', 72: '3 days', 168: '1 week' }[newInterval];
        setSuccess(`Auto-sync interval updated to every ${label}`);
      } catch (error) {
        setError('Failed to update interval');
      }
    }
  };

  return (
    <div className={`auth-container dashboard-container ${isVisible ? 'in-view' : ''}`}>
      <ParticleBackground />
      {IsDisabledS && <div className="disabled-all"></div>}
      <DialogS
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        api={syncResults.api}
        added={syncResults.added}
        updated={syncResults.updated}
      />

      <div className='dashboard-grid'>
        <div className="wrapper reveal reveal-left connections-panel">
          <h1 className="auth-title">Connections</h1>

          <div className="connections-group">
            <div className="connection-item">
              <button className="auth-button" onClick={handleCanvasButton} disabled={IsDisabledC} title={IsDisabledC ? "Already Linked" : ""}>
                {IsDisabledC ? "Linked Canvas" : "Link Canvas"}
              </button>
              <SiCanvas className='icon-api' />
            </div>

            {whichAPI ? (
              <div className="connection-item">
                <button className="auth-button" onClick={handleLinkTodoist} disabled={IsDisabledT} title={IsDisabledT ? "Already Linked" : ""}>
                  {IsDisabledT ? "Linked Todoist" : "Link Todoist"}
                </button>
                <SiTodoist className='icon-api' />
              </div>
            ) : (
              <div className="connection-item">
                <button className="auth-button" onClick={handleLinkNotion} disabled={IsDisabledN} title={IsDisabledN ? "Already Linked" : ""}>
                  {IsDisabledN ? "Linked Notion" : "Link Notion"}
                </button>
                <RxNotionLogo className='icon-api' />
              </div>
            )}
          </div>
        </div>

        <div className="wrapper reveal reveal-up main-panel">
          <h1 className="auth-title">Welcome, {userName}</h1>
          <div className="dashboard-content">
            <span className="step-heading">How to Get Started:</span>
            <ul className="theme-list">
              <li>Link Canvas and Todoist/Notion</li>
              <li>Click Sync To Process Tasks</li>
            </ul>

            <div className="info-box">
              <span className="step-heading2">Quick Tip</span>
              <p className="fyi">Change your preferred service in <Link to="/settings" className='settings-link'>Settings</Link></p>
            </div>

            <div className="history-section" style={{ marginTop: '40px' }}>
              <span className="step-heading">Recent Activity</span>
              <RecentActivity history={syncHistory} />
            </div>
          </div>
        </div>

        <div className="wrapper reveal reveal-right sync-panel">
          <h1 className="auth-title">Syncizer</h1>
          <div className="sync-content">
            <button
              className="auth-button sync-btn"
              onClick={handleSync}
              disabled={IsDisabledS || cooldown > 0}
              title={IsDisabledS ? "Currently Syncing" : (cooldown > 0 ? `Wait ${cooldown}s` : "")}
            >
              {cooldown > 0 ? `Sync Now (${cooldown}s)` : "Sync Now"}
            </button>
            <div className="sync-status">
              <FaSync className={`iconS ${IsDisabledS ? "rotating" : ""}`} />
            </div>
          </div>

          <div className="auto-sync-section">
            <div className="auto-sync-header">
              <IoMdTime className="auto-sync-icon" />
              <span className="auto-sync-label">Auto Sync</span>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={autoSync}
                  onChange={handleAutoSyncToggle}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
            {autoSync && (
              <div className="interval-selector">
                {[{ value: 24, label: '1 Day' }, { value: 72, label: '3 Days' }, { value: 168, label: '1 Week' }].map(opt => (
                  <button
                    key={opt.value}
                    className={`interval-btn ${syncInterval === opt.value ? 'active' : ''}`}
                    onClick={() => handleIntervalChange(opt.value)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
