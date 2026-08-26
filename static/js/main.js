// IBVAP Main Tactical JavaScript Client
document.addEventListener('DOMContentLoaded', () => {
    initWebSockets();
    initOSNotifications();
    updateLiveClock();
    setInterval(updateLiveClock, 1000);
});

// Live Clock Header
function updateLiveClock() {
    const clockEl = document.getElementById('live-system-clock');
    if (clockEl) {
        const now = new Date();
        clockEl.innerText = now.toUTCString().replace('GMT', 'UTC') + ' | ' + now.toLocaleTimeString();
    }
}

// Request HTML5 Desktop/Mobile System Notification Permission
function initOSNotifications() {
    if ('Notification' in window) {
        if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('[OS NOTIFY] Desktop system notifications enabled.');
                }
            });
        }
    }
}

// Display System OS Notification (Laptop / Mobile Notification Bar)
function triggerOSNotification(title, body, iconUrl) {
    if ('Notification' in window && Notification.permission === 'granted') {
        try {
            const notification = new Notification(title, {
                body: body,
                icon: iconUrl || '/static/snapshots/placeholder.png',
                tag: 'ibvap-security-alert',
                requireInteraction: true
            });
            notification.onclick = () => {
                window.focus();
                window.location.href = '/alerts';
            };
        } catch (e) {
            console.error('[OS NOTIFY] Failed to display system notification:', e);
        }
    }
}

// Web Audio API Alarm Synthesizer (No external mp3 required)
function playAudioAlarm(severity) {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        
        osc.type = severity === 'CRITICAL' ? 'sawtooth' : 'sine';
        osc.frequency.setValueAtTime(severity === 'CRITICAL' ? 880 : 600, ctx.currentTime); // A5 pitch
        osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.4);
        
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start();
        osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
        console.log('[AUDIO ALARM] Audio context error:', e);
    }
}

// WebSocket Connection & Real-Time Alert Event Listener
let socket = null;
function initWebSockets() {
    socket = io();

    socket.on('connect', () => {
        console.log('[WEBSOCKET] Connected to IBVAP Server');
        const statusEl = document.getElementById('ws-status-badge');
        if (statusEl) {
            statusEl.className = 'badge bg-success';
            statusEl.innerText = 'C2 ONLINE';
        }
    });

    socket.on('disconnect', () => {
        console.warn('[WEBSOCKET] Disconnected from server');
        const statusEl = document.getElementById('ws-status-badge');
        if (statusEl) {
            statusEl.className = 'badge bg-danger';
            statusEl.innerText = 'C2 OFFLINE';
        }
    });

    // Real-Time Incoming Alert Event
    socket.on('new_alert', (alertData) => {
        console.log('[NEW ALERT RECEIVED]', alertData);
        
        // 1. Play Audio Alarm
        playAudioAlarm(alertData.severity);
        
        // 2. Trigger OS System Notification (Laptop/Mobile notification bar)
        const notifyTitle = `🚨 ${alertData.severity} BORDER ALERT: ${alertData.event_type}`;
        const notifyBody = `${alertData.location} - ${alertData.description}`;
        triggerOSNotification(notifyTitle, notifyBody, alertData.snapshot_path);
        
        // 3. Update Navbar Notification Bell Counter
        const bellBadge = document.getElementById('navbar-bell-badge');
        if (bellBadge) {
            let count = parseInt(bellBadge.innerText || '0') + 1;
            bellBadge.innerText = count;
            bellBadge.classList.remove('d-none');
        }
        
        // 4. Append to Live Dashboard Alert Ticker if on Index page
        const tickerContainer = document.getElementById('live-alert-ticker');
        if (tickerContainer) {
            const card = document.createElement('div');
            card.className = `alert-item-card ${alertData.severity}`;
            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <span class="badge ${alertData.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">${alertData.severity}</span>
                    <small class="text-muted">${alertData.timestamp.split(' ')[1]}</small>
                </div>
                <div class="fw-bold mt-1 text-light">${alertData.event_type.replace('_', ' ')}</div>
                <small class="text-muted d-block">${alertData.camera_name} (${alertData.location})</small>
                <p class="small text-slate-300 mb-1 mt-1">${alertData.description}</p>
                <div class="d-flex gap-2 align-items-center mt-2">
                    ${alertData.snapshot_path ? `<a href="${alertData.snapshot_path}" target="_blank" class="btn btn-sm btn-outline-info py-0 px-2 small">View Snapshot</a>` : ''}
                    <button onclick="acknowledgeAlert(${alertData.id}, this)" class="btn btn-sm btn-outline-success py-0 px-2 small">Acknowledge</button>
                </div>
            `;
            tickerContainer.insertBefore(card, tickerContainer.firstChild);
            
            // Limit ticker items to 30
            if (tickerContainer.children.length > 30) {
                tickerContainer.removeChild(tickerContainer.lastChild);
            }
        }
    });
}

// REST API Helper to Acknowledge Alerts
function acknowledgeAlert(alertId, btnEl) {
    fetch(`/api/alerts/${alertId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'ACKNOWLEDGED' })
    })
    .then(res => res.json())
    .then(data => {
        if (btnEl) {
            btnEl.className = 'btn btn-sm btn-success disabled py-0 px-2 small';
            btnEl.innerText = 'Acknowledged';
        }
        // Decrement Bell Badge
        const bellBadge = document.getElementById('navbar-bell-badge');
        if (bellBadge) {
            let count = Math.max(0, parseInt(bellBadge.innerText || '0') - 1);
            bellBadge.innerText = count;
            if (count === 0) bellBadge.classList.add('d-none');
        }
    });
}
