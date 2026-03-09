const API_BASE = '/api';

export async function fetchLeads() {
    const res = await fetch(`${API_BASE}/leads/`);
    return res.json();
}

export async function fetchPipeline() {
    const res = await fetch(`${API_BASE}/leads/pipeline`);
    return res.json();
}

export async function fetchLeadDetail(leadId) {
    const res = await fetch(`${API_BASE}/leads/${leadId}`);
    return res.json();
}

export async function simulateMessage(channel, channelUserId, messageText) {
    const res = await fetch(`${API_BASE}/leads/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            channel,
            channel_user_id: channelUserId,
            message_text: messageText,
        }),
    });
    return res.json();
}

export async function fetchConversionAnalytics() {
    const res = await fetch(`${API_BASE}/analytics/conversion`);
    return res.json();
}

export async function fetchImprovementInsights() {
    const res = await fetch(`${API_BASE}/analytics/improvement`);
    return res.json();
}

export async function fetchAppointments() {
    const res = await fetch(`${API_BASE}/appointments/`);
    return res.json();
}

export async function checkAvailability(specialty) {
    const res = await fetch(`${API_BASE}/leads/availability/${specialty}`);
    return res.json();
}
