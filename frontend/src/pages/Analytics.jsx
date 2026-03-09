import React, { useEffect, useState } from 'react';
import { fetchConversionAnalytics } from '../api/client';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend,
} from 'recharts';

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe'];
const SCORE_COLORS = { hot: '#ef4444', warm: '#f59e0b', cold: '#3b82f6', unscored: '#64748b' };

export default function Analytics() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchConversionAnalytics()
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="spinner" />;
    if (!data) return <div className="empty-state"><p>No analytics data yet</p></div>;

    // Prepare chart data
    const channelData = Object.entries(data.by_channel || {}).map(([name, vals]) => ({
        name,
        captured: vals.captured,
        converted: vals.converted,
        rate: vals.conversion_rate,
    }));

    const scoreData = Object.entries(data.by_score || {}).map(([name, value]) => ({
        name,
        value,
    }));

    const serviceData = Object.entries(data.by_service || {}).map(([name, vals]) => ({
        name: name.length > 20 ? name.substring(0, 20) + '...' : name,
        captured: vals.captured,
        converted: vals.converted,
        rate: vals.conversion_rate,
    }));

    return (
        <div>
            <div className="page-header">
                <h2>Conversion Analytics</h2>
                <p>Track lead performance metrics across channels and services</p>
            </div>

            {/* Summary Stats */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-label">Total Leads</div>
                    <div className="stat-value">{data.total_leads}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Conversion Rate</div>
                    <div className="stat-value" style={{ color: 'var(--success)' }}>
                        {data.overall_conversion_rate}%
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Historical Baseline</div>
                    <div className="stat-value">{data.historical_baseline?.conversion_rate}%</div>
                    <div className="stat-change">
                        from {data.historical_baseline?.total_interactions} past interactions
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="charts-grid">
                {/* Channel Performance */}
                <div className="chart-card">
                    <h3>📊 Conversion by Channel</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={channelData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    background: '#1e293b',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: 8,
                                    color: '#f1f5f9',
                                }}
                            />
                            <Bar dataKey="captured" fill="#6366f1" name="Captured" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="converted" fill="#10b981" name="Converted" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Score Distribution */}
                <div className="chart-card">
                    <h3>🎯 Lead Score Distribution</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie
                                data={scoreData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                paddingAngle={5}
                                dataKey="value"
                                label={({ name, value }) => `${name}: ${value}`}
                            >
                                {scoreData.map((entry) => (
                                    <Cell key={entry.name} fill={SCORE_COLORS[entry.name] || '#64748b'} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Service Performance */}
                <div className="chart-card" style={{ gridColumn: 'span 2' }}>
                    <h3>🏥 Conversion by Service Type</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={serviceData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis type="number" stroke="#64748b" fontSize={12} />
                            <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} width={150} />
                            <Tooltip
                                contentStyle={{
                                    background: '#1e293b',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: 8,
                                    color: '#f1f5f9',
                                }}
                            />
                            <Bar dataKey="captured" fill="#8b5cf6" name="Captured" radius={[0, 4, 4, 0]} />
                            <Bar dataKey="converted" fill="#10b981" name="Converted" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
