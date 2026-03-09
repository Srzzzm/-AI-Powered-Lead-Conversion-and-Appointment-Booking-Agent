import React, { useState } from 'react';
import { simulateMessage } from '../api/client';

const SAMPLE_MESSAGES = [
    { channel: 'whatsapp', id: '+919876543210', msg: 'I need knee replacement surgery urgently. My doctor recommended it last week. I have Star Health insurance.' },
    { channel: 'instagram', id: 'user_rahul_v', msg: 'Do you offer dental implants? What\'s the cost?' },
    { channel: 'whatsapp', id: '+919634567890', msg: 'I need an MRI scan for my lower back. Can I book for tomorrow? I\'ll pay myself.' },
    { channel: 'instagram', id: 'user_arjun_p', msg: 'Need cardiac checkup asap. Father had heart attack history. I\'m 45 and getting chest pains.' },
    { channel: 'whatsapp', id: '+919723456789', msg: 'Just browsing. What specialties does your hospital have?' },
];

export default function SimulatePage() {
    const [channel, setChannel] = useState('whatsapp');
    const [userId, setUserId] = useState('+919876543210');
    const [message, setMessage] = useState('');
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState([]);

    async function handleSubmit(e) {
        e.preventDefault();
        if (!message.trim()) return;

        setLoading(true);
        try {
            const result = await simulateMessage(channel, userId, message);
            setResponse(result);
            setHistory(prev => [...prev, { sent: message, received: result, channel }]);
            setMessage('');
        } catch (err) {
            setResponse({ error: err.message });
        } finally {
            setLoading(false);
        }
    }

    function loadSample(sample) {
        setChannel(sample.channel);
        setUserId(sample.id);
        setMessage(sample.msg);
    }

    return (
        <div>
            <div className="page-header">
                <h2>Simulate Incoming Lead</h2>
                <p>Test the AI agent by simulating messages from different channels</p>
            </div>

            {/* Quick templates */}
            <div style={{ marginBottom: 24 }}>
                <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                    Quick Templates
                </p>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {SAMPLE_MESSAGES.map((s, i) => (
                        <button
                            key={i}
                            className="btn btn-secondary"
                            style={{ fontSize: 12 }}
                            onClick={() => loadSample(s)}
                        >
                            <span className={`badge badge-${s.channel}`} style={{ fontSize: 10 }}>{s.channel}</span>
                            {s.msg.substring(0, 40)}...
                        </button>
                    ))}
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                {/* Input Form */}
                <div className="simulate-panel">
                    <h3>📨 Send Message</h3>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Channel</label>
                            <select value={channel} onChange={e => setChannel(e.target.value)}>
                                <option value="whatsapp">WhatsApp</option>
                                <option value="instagram">Instagram</option>
                                <option value="webchat">Web Chat</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>User ID (phone or username)</label>
                            <input
                                type="text"
                                value={userId}
                                onChange={e => setUserId(e.target.value)}
                                placeholder="e.g. +919876543210"
                            />
                        </div>
                        <div className="form-group">
                            <label>Message</label>
                            <textarea
                                value={message}
                                onChange={e => setMessage(e.target.value)}
                                placeholder="Type the patient's message here..."
                                rows={4}
                            />
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? '⏳ Processing...' : '🚀 Send Message'}
                        </button>
                    </form>

                    {response && (
                        <div className="response-panel">
                            <h4>✅ Agent Response</h4>
                            <pre>{JSON.stringify(response, null, 2)}</pre>
                        </div>
                    )}
                </div>

                {/* Conversation Simulation View */}
                <div className="chat-view" style={{ maxHeight: '65vh' }}>
                    <div className="chat-header">
                        <div className="avatar">🤖</div>
                        <div>
                            <h4 style={{ fontSize: 15, fontWeight: 600 }}>Live Simulation</h4>
                            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                {channel} • {userId}
                            </p>
                        </div>
                    </div>
                    <div className="chat-messages">
                        {history.length === 0 ? (
                            <div className="empty-state"><p>Send a message to start the simulation</p></div>
                        ) : (
                            history.map((h, i) => (
                                <React.Fragment key={i}>
                                    <div className="chat-bubble user">{h.sent}</div>
                                    <div className="chat-bubble agent">
                                        {h.received?.agent_response || JSON.stringify(h.received)}
                                        <span className="time">
                                            🤖 AI Agent • Lead #{h.received?.lead_id} • {h.received?.status}
                                        </span>
                                    </div>
                                </React.Fragment>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
