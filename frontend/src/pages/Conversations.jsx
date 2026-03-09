import React, { useEffect, useState } from 'react';
import { fetchLeads, fetchLeadDetail } from '../api/client';

export default function Conversations() {
    const [leads, setLeads] = useState([]);
    const [selectedLead, setSelectedLead] = useState(null);
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLeads()
            .then(data => {
                setLeads(data);
                setLoading(false);
            })
            .catch(console.error);
    }, []);

    async function selectLead(lead) {
        setSelectedLead(lead);
        try {
            const data = await fetchLeadDetail(lead.id);
            setDetail(data);
        } catch (err) {
            console.error(err);
        }
    }

    if (loading) return <div className="spinner" />;

    return (
        <div>
            <div className="page-header">
                <h2>Conversation Logs</h2>
                <p>View full chat history for each lead</p>
            </div>

            <div className="conversation-layout">
                {/* Lead List */}
                <div className="lead-list">
                    <div className="lead-list-header">All Leads ({leads.length})</div>
                    {leads.map(lead => (
                        <div
                            key={lead.id}
                            className={`lead-list-item ${selectedLead?.id === lead.id ? 'active' : ''}`}
                            onClick={() => selectLead(lead)}
                        >
                            <div className="avatar">
                                {(lead.name || '?')[0].toUpperCase()}
                            </div>
                            <div className="lead-info">
                                <h4>{lead.name || 'Unknown'}</h4>
                                <p>{lead.service_interest || 'General'} • {lead.channel}</p>
                            </div>
                            {lead.score && (
                                <span className={`badge badge-${lead.score}`}>{lead.score}</span>
                            )}
                        </div>
                    ))}
                    {leads.length === 0 && (
                        <div className="empty-state"><p>No leads yet. Simulate one first!</p></div>
                    )}
                </div>

                {/* Chat View */}
                <div className="chat-view">
                    {detail ? (
                        <>
                            <div className="chat-header">
                                <div className="avatar" style={{ width: 40, height: 40, fontSize: 16 }}>
                                    {(detail.lead.name || '?')[0].toUpperCase()}
                                </div>
                                <div>
                                    <h4 style={{ fontSize: 15, fontWeight: 600 }}>{detail.lead.name || 'Unknown'}</h4>
                                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                        {detail.lead.service_interest} • {detail.lead.channel} •{' '}
                                        <span className={`badge badge-${detail.lead.score || 'cold'}`} style={{ fontSize: 10 }}>
                                            {detail.lead.score || 'unscored'}
                                        </span>
                                    </p>
                                </div>
                            </div>
                            <div className="chat-messages">
                                {detail.conversations.length > 0 ? (
                                    detail.conversations.map(msg => (
                                        <div key={msg.id} className={`chat-bubble ${msg.sender}`}>
                                            {msg.message}
                                            <span className="time">
                                                {msg.sender === 'agent' ? '🤖 AI Agent' : '👤 Patient'} • {msg.created_at?.slice(11, 16) || ''}
                                            </span>
                                        </div>
                                    ))
                                ) : (
                                    <div className="empty-state"><p>No messages yet</p></div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="empty-state" style={{ margin: 'auto' }}>
                            <p>Select a lead to view their conversation</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
