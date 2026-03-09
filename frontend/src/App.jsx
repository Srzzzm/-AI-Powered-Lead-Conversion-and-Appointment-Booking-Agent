import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Conversations from './pages/Conversations';
import Insights from './pages/Insights';
import SimulatePage from './pages/SimulatePage';

export default function App() {
    return (
        <BrowserRouter>
            <div className="app-layout">
                <Sidebar />
                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/analytics" element={<Analytics />} />
                        <Route path="/conversations" element={<Conversations />} />
                        <Route path="/insights" element={<Insights />} />
                        <Route path="/simulate" element={<SimulatePage />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}

function Sidebar() {
    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="brand-icon">🏥</div>
                <div>
                    <h1>HealthFirst AI</h1>
                    <span>Lead Conversion Agent</span>
                </div>
            </div>
            <nav>
                <ul className="nav-links">
                    <li>
                        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>
                            Pipeline Dashboard
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/analytics" className={({ isActive }) => isActive ? 'active' : ''}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 20V10M12 20V4M6 20v-6" /></svg>
                            Analytics
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/conversations" className={({ isActive }) => isActive ? 'active' : ''}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" /></svg>
                            Conversations
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/insights" className={({ isActive }) => isActive ? 'active' : ''}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
                            AI Insights
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/simulate" className={({ isActive }) => isActive ? 'active' : ''}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
                            Simulate Lead
                        </NavLink>
                    </li>
                </ul>
            </nav>
        </aside>
    );
}
