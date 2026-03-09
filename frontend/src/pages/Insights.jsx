import React, { useEffect, useState } from 'react';
import { fetchImprovementInsights } from '../api/client';

export default function Insights() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchImprovementInsights()
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="spinner" />;
    if (!data) return <div className="empty-state"><p>No insights data yet</p></div>;

    return (
        <div>
            <div className="page-header">
                <h2>AI Continuous Improvement Insights</h2>
                <p>Adaptive learning module analyzing conversion patterns</p>
            </div>

            <div className="insights-grid">
                {/* Response Time Insight */}
                <div className="insight-card">
                    <h4>⚡ Response Time Analysis</h4>
                    <div style={{ display: 'flex', gap: 24, marginBottom: 12 }}>
                        <div>
                            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--success)' }}>
                                {data.response_time_insight?.avg_response_time_converted_sec}s
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Avg for Converted</div>
                        </div>
                        <div>
                            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--hot)' }}>
                                {data.response_time_insight?.avg_response_time_lost_sec}s
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Avg for Lost</div>
                        </div>
                    </div>
                    <p>{data.response_time_insight?.recommendation}</p>
                </div>

                {/* Top Converting Sequences */}
                <div className="insight-card">
                    <h4>🏆 Top Converting Question Sequences</h4>
                    {data.top_converting_sequences?.map((seq, i) => (
                        <div key={i} style={{ marginBottom: 12 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                                Sequence {i + 1} ({seq.conversions} conversions)
                            </div>
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                {seq.questions.map((q, j) => (
                                    <span key={j} className="badge" style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--accent-primary)' }}>
                                        {q}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Channel Insight */}
                <div className="insight-card">
                    <h4>📱 Best Converting Channels</h4>
                    {data.channel_insight && Object.entries(data.channel_insight).map(([channel, count]) => (
                        <div key={channel} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
                            <span className={`badge badge-${channel}`}>{channel}</span>
                            <span style={{ fontWeight: 700, color: 'var(--success)' }}>{count} conversions</span>
                        </div>
                    ))}
                </div>

                {/* Recommendations */}
                <div className="insight-card" style={{ gridColumn: 'span 2' }}>
                    <h4>💡 AI Recommendations</h4>
                    <ul>
                        {data.recommendations?.map((rec, i) => (
                            <li key={i}>{rec}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
}
