import React from 'react';
import { SiTodoist, SiNotion } from 'react-icons/si';
import { FaHistory } from 'react-icons/fa';
import './RecentActivity.css';

const RecentActivity = ({ history }) => {
    const formatRelativeTime = (isoString) => {
        const date = new Date(isoString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    };

    if (!history || history.length === 0) {
        return (
            <div className="recent-activity-empty">
                <FaHistory className="empty-icon" />
                <p>No sync activity yet.</p>
            </div>
        );
    }

    return (
        <div className="recent-activity-container">
            <div className="activity-list">
                {history.map((log, index) => (
                    <div key={index} className="activity-item">
                        <div className="activity-icon-col">
                            {log.service === 'Todoist' ? (
                                <SiTodoist className="service-icon todoist" />
                            ) : (
                                <SiNotion className="service-icon notion" />
                            )}
                        </div>
                        <div className="activity-details">
                            <div className="activity-header">
                                <span className="activity-service">{log.service} Sync</span>
                                <span className="activity-time">{formatRelativeTime(log.timestamp)}</span>
                            </div>
                            <div className="activity-stats">
                                <span className="stat-added">+{log.added} added</span>
                                <span className="stat-separator">•</span>
                                <span className="stat-updated">{log.updated} updated</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default RecentActivity;
