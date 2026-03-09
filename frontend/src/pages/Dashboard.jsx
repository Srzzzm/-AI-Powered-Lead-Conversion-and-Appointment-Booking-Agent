import React, { useEffect, useState } from 'react';
import { fetchPipeline, fetchLeads } from '../api/client';

const PIPELINE_STAGES = [
    { key: 'captured', label: 'Captured', emoji: '📥' },
    { key: 'qualifying', label: 'Qualifying', emoji: '💬' },
    { key: 'qualified', label: 'Qualified', emoji: '✅' },
    { key: 'converted', label: 'Converted', emoji: '🎉' },
    { key: 'nurturing', label: 'Nurturing', emoji: '🌱' },
    { key: 'lost', label: 'Lost', emoji: '❌' },
];

export default function Dashboard() {
    const [pipeline, setPipeline] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 5000); // poll every 5s
        return () => clearInterval(interval);
    }, []);

    async function loadData() {
        try {
            const [pipelineData, leadsData] = await Promise.all([
                fetchPipeline(),
                fetchLeads(),
            ]);
            setPipeline(pipelineData);

            const total = leadsData.length;
            const converted = leadsData.filter(l => l.status === 'converted').length;
            const hot = leadsData.filter(l => l.score === 'hot').length;
            const warm = leadsData.filter(l => l.score === 'warm').length;
            const cold = leadsData.filter(l => l.score === 'cold').length;

            setStats({
                total,
                converted,
                hot,
                warm,
                cold,
                conversionRate: total > 0 ? ((converted / total) * 100).toFixed(1) : '0.0',
            });
        } catch (err) {
            console.error('Failed to load pipeline:', err);
        } finally {
            setLoading(false);
        }
    }

    if (loading) return <div className="spinner" />;

    return (
        <div>
            <div className="page-header">
                <h2>Lead Pipeline Dashboard</h2>
                <p>Real-time view of all healthcare leads across channels</p>
            </div>

            {/* Stats */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-label">Total Leads</div>
                    <div className="stat-value">{stats?.total || 0}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Converted</div>
                    <div className="stat-value" style={{ color: 'var(--success)' }}>{stats?.converted || 0}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Conversion Rate</div>
                    <div className="stat-value">{stats?.conversionRate || 0}%</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">🔥 Hot</div>
                    <div className="stat-value" style={{ color: 'var(--hot)' }}>{stats?.hot || 0}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">🌤️ Warm</div>
                    <div className="stat-value" style={{ color: 'var(--warm)' }}>{stats?.warm || 0}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">❄️ Cold</div>
                    <div className="stat-value" style={{ color: 'var(--cold)' }}>{stats?.cold || 0}</div>
                </div>
            </div>

            {/* Pipeline Kanban Board */}
            <div className="pipeline-board">
                {PIPELINE_STAGES.map(stage => (
                    <PipelineColumn
                        key={stage.key}
                        stage={stage}
                        leads={pipeline?.[stage.key] || []}
                    />
                ))}
            </div>
        </div>
    );
}

function PipelineColumn({ stage, leads }) {
    return (
        <div className="pipeline-column">
            <div className="pipeline-column-header">
                <h3>{stage.emoji} {stage.label}</h3>
                <span className="count">{leads.length}</span>
            </div>
            {leads.length === 0 ? (
                <div className="empty-state"><p>No leads</p></div>
            ) : (
                leads.map(lead => <LeadCard key={lead.id} lead={lead} />)
            )}
        </div>
    );
}

function LeadCard({ lead }) {
    const channelClass = `badge-${lead.channel}`;
    const scoreClass = lead.score ? `badge-${lead.score}` : '';

    return (
        <div className="lead-card">
            <div className="lead-name">{lead.name || 'Unknown'}</div>
            <div className="lead-service">{lead.service_interest || 'General Inquiry'}</div>
            <div className="lead-meta">
                <span className={`badge ${channelClass}`}>{lead.channel}</span>
                {lead.score && <span className={`badge ${scoreClass}`}>{lead.score}</span>}
                {lead.urgency && (
                    <span className="badge" style={{
                        background: lead.urgency === 'high' ? 'var(--hot-bg)' : 'var(--bg-glass)',
                        color: lead.urgency === 'high' ? 'var(--hot)' : 'var(--text-muted)',
                    }}>
                        {lead.urgency === 'high' ? '⚡' : ''} {lead.urgency}
                    </span>
                )}
            </div>
        </div>
    );
}
