# 🌐 Frontend WebSocket Integration Guide for SafeHorizon

**Complete guide for frontend developers integrating WebSocket real-time alerts with SafeHorizon API**

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Common Frontend Errors](#-common-frontend-errors)
3. [Authentication Issues](#-authentication-issues)
4. [Connection Problems](#-connection-problems)
5. [Browser-Specific Issues](#-browser-specific-issues)
6. [Complete Implementation Examples](#-complete-implementation-examples)
7. [Testing Your WebSocket](#-testing-your-websocket)
8. [Production Best Practices](#-production-best-practices)
9. [Debugging Tools](#-debugging-tools)

---

## 🚀 Quick Start

### Minimum Working Example

```javascript
// 1. Get your JWT token from login
const token = "your_jwt_token_here"; // From /api/auth/login response

// 2. Determine the correct WebSocket URL
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host; // e.g., "localhost:8000" or "api.safehorizon.com"
const wsUrl = `${protocol}//${host}/api/alerts/subscribe?token=${token}`;

// 3. Create WebSocket connection
const websocket = new WebSocket(wsUrl);

// 4. Handle connection events
websocket.onopen = () => {
    console.log("✅ Connected to SafeHorizon alerts");
};

websocket.onmessage = (event) => {
    if (event.data === "pong") return; // Ignore heartbeat responses
    
    const alert = JSON.parse(event.data);
    console.log("🚨 New alert:", alert);
    // Display alert in your UI
};

websocket.onerror = (error) => {
    console.error("❌ WebSocket error:", error);
};

websocket.onclose = (event) => {
    console.log(`Connection closed: ${event.code} - ${event.reason}`);
};
```

---

## ❌ Common Frontend Errors

### Error 1: "WebSocket connection to 'ws://...' failed"

**What you see in console:**
```
WebSocket connection to 'ws://localhost:8000/api/alerts/subscribe' failed: 
Error during WebSocket handshake: Unexpected response code: 403
```

**Causes:**
1. Missing authentication token
2. Invalid token format
3. Token in wrong location (headers instead of query params)
4. CORS issues

**Solutions:**

```javascript
// ❌ WRONG: Token in headers (doesn't work with WebSocket)
const ws = new WebSocket('ws://localhost:8000/api/alerts/subscribe', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// ❌ WRONG: No token at all
const ws = new WebSocket('ws://localhost:8000/api/alerts/subscribe');

// ✅ CORRECT: Token in query parameter
const ws = new WebSocket(`ws://localhost:8000/api/alerts/subscribe?token=${token}`);
```

---

### Error 2: "WebSocket is closed before the connection is established"

**What you see:**
```
WebSocket connection closed immediately
Code: 1006 (Abnormal Closure)
```

**Causes:**
1. Server not running
2. Wrong port or URL
3. CORS/firewall blocking connection
4. SSL/TLS certificate issues (for wss://)

**Solutions:**

```javascript
// Check if server is running first
fetch('http://localhost:8000/docs')
    .then(response => {
        if (response.ok) {
            console.log("✅ Server is running");
            // Now try WebSocket
            connectWebSocket();
        }
    })
    .catch(error => {
        console.error("❌ Server is not reachable:", error);
    });

// Verify correct URL construction
function getWebSocketUrl(token) {
    // For local development
    if (window.location.hostname === 'localhost') {
        return `ws://localhost:8000/api/alerts/subscribe?token=${token}`;
    }
    
    // For production
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/api/alerts/subscribe?token=${token}`;
}
```

---

### Error 3: "Received close code 1008 (Policy Violation)"

**What you see:**
```
WebSocket closed: 1008 - Invalid token
WebSocket closed: 1008 - Access denied: Authority role required
```

**Causes:**
1. Token expired
2. Wrong user role (tourist trying to access authority endpoint)
3. Malformed token
4. User doesn't exist in database

**Solutions:**

```javascript
// Check token before connecting
function isTokenExpired(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds
        return Date.now() > exp;
    } catch (e) {
        console.error("Invalid token format:", e);
        return true;
    }
}

// Verify role before connecting
function canAccessWebSocket(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const role = payload.role;
        
        if (!['authority', 'admin'].includes(role)) {
            console.error(`❌ Access denied: ${role} role cannot access WebSocket`);
            return false;
        }
        
        return true;
    } catch (e) {
        console.error("Cannot verify token:", e);
        return false;
    }
}

// Use before connecting
if (isTokenExpired(token)) {
    console.error("❌ Token expired, please login again");
    // Redirect to login page
    window.location.href = '/login';
} else if (!canAccessWebSocket(token)) {
    console.error("❌ Insufficient permissions");
} else {
    // Connect to WebSocket
    connectWebSocket(token);
}
```

---

### Error 4: "WebSocket messages not being received"

**What you see:**
- Connection opens successfully
- No alerts received
- No errors in console

**Causes:**
1. Not listening to correct event
2. JSON parsing errors
3. No alerts being triggered on server
4. Connection silently dropped

**Solutions:**

```javascript
let ws = null;
let heartbeatInterval = null;

function connectWebSocket(token) {
    ws = new WebSocket(`ws://localhost:8000/api/alerts/subscribe?token=${token}`);
    
    ws.onopen = () => {
        console.log("✅ WebSocket connected");
        
        // Start heartbeat to keep connection alive
        heartbeatInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                console.log("💓 Sending heartbeat...");
                ws.send("ping");
            }
        }, 30000); // Every 30 seconds
    };
    
    ws.onmessage = (event) => {
        console.log("📨 Raw message received:", event.data);
        
        // Handle heartbeat response
        if (event.data === "pong") {
            console.log("💗 Heartbeat acknowledged");
            return;
        }
        
        // Parse alert
        try {
            const alert = JSON.parse(event.data);
            console.log("🚨 Alert parsed:", alert);
            handleAlert(alert);
        } catch (e) {
            console.error("❌ Failed to parse alert:", e, event.data);
        }
    };
    
    ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
    };
    
    ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed: ${event.code} - ${event.reason}`);
        clearInterval(heartbeatInterval);
        
        // Auto-reconnect for non-auth errors
        if (event.code !== 1008) {
            console.log("🔄 Reconnecting in 5 seconds...");
            setTimeout(() => connectWebSocket(token), 5000);
        }
    };
}
```

---

## 🔐 Authentication Issues

### Problem: "How do I get the authentication token?"

**Complete Authentication Flow:**

```javascript
// Step 1: Login to get token
async function login(email, password) {
    try {
        const response = await fetch('http://localhost:8000/api/auth/login-authority', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            throw new Error(`Login failed: ${response.status}`);
        }
        
        const data = await response.json();
        const token = data.access_token;
        
        // Store token for later use
        localStorage.setItem('auth_token', token);
        
        console.log("✅ Login successful");
        return token;
        
    } catch (error) {
        console.error("❌ Login error:", error);
        throw error;
    }
}

// Step 2: Use token to connect WebSocket
async function initializeWebSocket() {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        console.error("❌ No token found, please login first");
        window.location.href = '/login';
        return;
    }
    
    // Verify token is still valid
    if (isTokenExpired(token)) {
        console.error("❌ Token expired, logging out...");
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
        return;
    }
    
    // Connect WebSocket
    connectWebSocket(token);
}

// Usage
login('authority@example.com', 'password123')
    .then(token => {
        initializeWebSocket();
    })
    .catch(error => {
        console.error("Failed to initialize:", error);
    });
```

---

### Problem: "Token expired during active session"

**Solution with automatic refresh:**

```javascript
class SafeHorizonWebSocket {
    constructor() {
        this.ws = null;
        this.token = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    async refreshToken() {
        // Implement token refresh logic
        try {
            const response = await fetch('http://localhost:8000/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                localStorage.setItem('auth_token', this.token);
                return true;
            }
            return false;
        } catch (e) {
            console.error("Token refresh failed:", e);
            return false;
        }
    }
    
    async connect() {
        this.token = localStorage.getItem('auth_token');
        
        if (!this.token) {
            console.error("No token available");
            return;
        }
        
        // Check if token is expired
        if (isTokenExpired(this.token)) {
            console.log("Token expired, attempting refresh...");
            const refreshed = await this.refreshToken();
            
            if (!refreshed) {
                console.error("Cannot refresh token, please login again");
                window.location.href = '/login';
                return;
            }
        }
        
        const wsUrl = `ws://localhost:8000/api/alerts/subscribe?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log("✅ Connected");
            this.reconnectAttempts = 0;
        };
        
        this.ws.onclose = (event) => {
            if (event.code === 1008) {
                console.log("Authentication failed, attempting token refresh...");
                this.refreshToken().then(success => {
                    if (success) {
                        this.connect(); // Reconnect with new token
                    } else {
                        window.location.href = '/login';
                    }
                });
            }
        };
    }
}
```

---

## 🔌 Connection Problems

### Problem: "Mixed Content - HTTP page accessing WSS"

**Error:**
```
Mixed Content: The page at 'https://app.safehorizon.com' was loaded over HTTPS, 
but attempted to connect to the insecure WebSocket endpoint 'ws://api.safehorizon.com/...'
```

**Solution:**

```javascript
// Automatic protocol detection
function getWebSocketUrl(token) {
    // Match the page's protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    return `${protocol}//${host}/api/alerts/subscribe?token=${token}`;
}

// For different API domain
function getWebSocketUrl(token) {
    const apiHost = process.env.REACT_APP_API_HOST || 'localhost:8000';
    const protocol = apiHost.includes('localhost') ? 'ws:' : 'wss:';
    
    return `${protocol}//${apiHost}/api/alerts/subscribe?token=${token}`;
}
```

---

### Problem: "Connection drops randomly"

**Solution with reconnection logic:**

```javascript
class ReliableWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = options.reconnectInterval || 3000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectAttempts = 0;
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.onMessageCallback = options.onMessage || (() => {});
        this.onErrorCallback = options.onError || (() => {});
    }
    
    connect() {
        console.log(`🔌 Connecting to ${this.url}...`);
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log("✅ Connected");
            this.reconnectAttempts = 0;
            this.startHeartbeat();
        };
        
        this.ws.onmessage = (event) => {
            if (event.data === "pong") {
                this.resetHeartbeatTimeout();
                return;
            }
            
            try {
                const data = JSON.parse(event.data);
                this.onMessageCallback(data);
            } catch (e) {
                console.error("Parse error:", e);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error("❌ WebSocket error:", error);
            this.onErrorCallback(error);
        };
        
        this.ws.onclose = (event) => {
            console.log(`🔌 Connection closed: ${event.code}`);
            this.stopHeartbeat();
            
            // Don't reconnect for authentication failures
            if (event.code === 1008) {
                console.error("Authentication failed, not reconnecting");
                return;
            }
            
            this.reconnect();
        };
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send("ping");
                this.setHeartbeatTimeout();
            }
        }, 30000);
    }
    
    setHeartbeatTimeout() {
        this.heartbeatTimeout = setTimeout(() => {
            console.warn("⚠️ Heartbeat timeout, closing connection");
            this.ws.close();
        }, 5000);
    }
    
    resetHeartbeatTimeout() {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
        }
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error("❌ Max reconnection attempts reached");
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);
        
        console.log(`🔄 Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000, "User disconnected");
        }
    }
}

// Usage
const token = localStorage.getItem('auth_token');
const wsUrl = `ws://localhost:8000/api/alerts/subscribe?token=${token}`;

const reliableWs = new ReliableWebSocket(wsUrl, {
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
    onMessage: (alert) => {
        console.log("🚨 Alert received:", alert);
        displayAlert(alert);
    },
    onError: (error) => {
        showNotification("Connection error", "error");
    }
});

reliableWs.connect();
```

---

## 🌍 Browser-Specific Issues

### Chrome/Edge
**Issue:** DevTools shows "101 Switching Protocols" but no messages
**Solution:** Check Console tab for JavaScript errors in message handlers

```javascript
// Add comprehensive error logging
ws.onmessage = (event) => {
    console.log("Raw data:", event.data);
    console.log("Data type:", typeof event.data);
    
    try {
        const parsed = JSON.parse(event.data);
        console.log("Parsed successfully:", parsed);
    } catch (e) {
        console.error("Parse failed:", e.message);
        console.error("Stack:", e.stack);
    }
};
```

### Firefox
**Issue:** WebSocket connections blocked by tracking protection
**Solution:** Whitelist your API domain or disable tracking protection for localhost

### Safari
**Issue:** WebSocket closes after page goes to background
**Solution:** Implement reconnection when page becomes visible

```javascript
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        console.log("Page visible, checking WebSocket...");
        
        if (ws.readyState !== WebSocket.OPEN) {
            console.log("Reconnecting...");
            connectWebSocket(token);
        }
    }
});
```

---

## 💻 Complete Implementation Examples

### React Implementation

```javascript
import { useState, useEffect, useRef, useCallback } from 'react';

function useWebSocket(token) {
    const [alerts, setAlerts] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState(null);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    
    const connect = useCallback(() => {
        if (!token) {
            setError("No authentication token");
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/api/alerts/subscribe?token=${token}`;
        
        console.log("Connecting to:", wsUrl);
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
            console.log("✅ WebSocket connected");
            setIsConnected(true);
            setError(null);
        };
        
        wsRef.current.onmessage = (event) => {
            if (event.data === "pong") return;
            
            try {
                const alert = JSON.parse(event.data);
                setAlerts(prev => [alert, ...prev]);
            } catch (e) {
                console.error("Failed to parse alert:", e);
            }
        };
        
        wsRef.current.onerror = (error) => {
            console.error("WebSocket error:", error);
            setError("Connection error");
        };
        
        wsRef.current.onclose = (event) => {
            console.log(`Connection closed: ${event.code}`);
            setIsConnected(false);
            
            // Reconnect for non-auth errors
            if (event.code !== 1008) {
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log("Reconnecting...");
                    connect();
                }, 3000);
            } else {
                setError("Authentication failed");
            }
        };
    }, [token]);
    
    useEffect(() => {
        connect();
        
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close(1000);
            }
        };
    }, [connect]);
    
    return { alerts, isConnected, error };
}

// Usage in component
function PoliceAlerts() {
    const token = localStorage.getItem('auth_token');
    const { alerts, isConnected, error } = useWebSocket(token);
    
    return (
        <div className="alerts-dashboard">
            <div className="connection-status">
                {isConnected ? (
                    <span className="status-connected">🟢 Connected</span>
                ) : (
                    <span className="status-disconnected">🔴 Disconnected</span>
                )}
                {error && <span className="error">{error}</span>}
            </div>
            
            <div className="alerts-list">
                <h2>Recent Alerts ({alerts.length})</h2>
                {alerts.map((alert, index) => (
                    <div key={index} className={`alert alert-${alert.severity}`}>
                        <h3>{alert.type}</h3>
                        <p>Tourist: {alert.tourist_name}</p>
                        <p>Time: {new Date(alert.timestamp).toLocaleString()}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
```

### Vue.js Implementation

```javascript
<template>
  <div class="alerts-dashboard">
    <div class="connection-status">
      <span v-if="isConnected" class="connected">🟢 Connected</span>
      <span v-else class="disconnected">🔴 Disconnected</span>
      <span v-if="error" class="error">{{ error }}</span>
    </div>
    
    <div class="alerts-list">
      <h2>Recent Alerts ({{ alerts.length }})</h2>
      <div 
        v-for="(alert, index) in alerts" 
        :key="index"
        :class="['alert', `alert-${alert.severity}`]"
      >
        <h3>{{ alert.type }}</h3>
        <p>Tourist: {{ alert.tourist_name }}</p>
        <p>Time: {{ formatTime(alert.timestamp) }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      ws: null,
      alerts: [],
      isConnected: false,
      error: null,
    };
  },
  
  mounted() {
    this.connectWebSocket();
  },
  
  beforeUnmount() {
    if (this.ws) {
      this.ws.close(1000);
    }
  },
  
  methods: {
    connectWebSocket() {
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        this.error = "No authentication token";
        return;
      }
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/alerts/subscribe?token=${token}`;
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log("✅ Connected");
        this.isConnected = true;
        this.error = null;
      };
      
      this.ws.onmessage = (event) => {
        if (event.data === "pong") return;
        
        try {
          const alert = JSON.parse(event.data);
          this.alerts.unshift(alert);
        } catch (e) {
          console.error("Parse error:", e);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.error = "Connection error";
      };
      
      this.ws.onclose = (event) => {
        this.isConnected = false;
        
        if (event.code !== 1008) {
          setTimeout(() => this.connectWebSocket(), 3000);
        } else {
          this.error = "Authentication failed";
        }
      };
    },
    
    formatTime(timestamp) {
      return new Date(timestamp).toLocaleString();
    }
  }
};
</script>
```

### Vanilla JavaScript Implementation

```javascript
class SafeHorizonAlerts {
    constructor(containerId, token) {
        this.container = document.getElementById(containerId);
        this.token = token;
        this.ws = null;
        this.alerts = [];
        
        this.init();
    }
    
    init() {
        this.createUI();
        this.connectWebSocket();
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="alerts-header">
                <h2>Real-Time Alerts</h2>
                <div class="status" id="connection-status">
                    <span class="status-dot">🔴</span>
                    <span class="status-text">Connecting...</span>
                </div>
            </div>
            <div class="alerts-container" id="alerts-list">
                <p class="no-alerts">Waiting for alerts...</p>
            </div>
        `;
    }
    
    updateStatus(connected, message = '') {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.innerHTML = `
                <span class="status-dot">🟢</span>
                <span class="status-text">Connected</span>
            `;
        } else {
            statusElement.innerHTML = `
                <span class="status-dot">🔴</span>
                <span class="status-text">${message || 'Disconnected'}</span>
            `;
        }
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/alerts/subscribe?token=${this.token}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log("✅ Connected");
            this.updateStatus(true);
        };
        
        this.ws.onmessage = (event) => {
            if (event.data === "pong") return;
            
            try {
                const alert = JSON.parse(event.data);
                this.addAlert(alert);
            } catch (e) {
                console.error("Parse error:", e);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error("WebSocket error:", error);
            this.updateStatus(false, 'Connection error');
        };
        
        this.ws.onclose = (event) => {
            console.log(`Connection closed: ${event.code}`);
            this.updateStatus(false, event.reason || 'Connection closed');
            
            if (event.code !== 1008) {
                setTimeout(() => this.connectWebSocket(), 3000);
            }
        };
    }
    
    addAlert(alert) {
        const alertsList = document.getElementById('alerts-list');
        
        // Remove "no alerts" message
        const noAlerts = alertsList.querySelector('.no-alerts');
        if (noAlerts) {
            noAlerts.remove();
        }
        
        // Create alert element
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${alert.severity}`;
        alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-type">${alert.type}</span>
                <span class="alert-time">${new Date(alert.timestamp).toLocaleString()}</span>
            </div>
            <div class="alert-body">
                <p><strong>Tourist:</strong> ${alert.tourist_name}</p>
                <p><strong>Severity:</strong> ${alert.severity}</p>
                ${alert.location ? `<p><strong>Location:</strong> ${alert.location}</p>` : ''}
            </div>
        `;
        
        // Add to top of list
        alertsList.insertBefore(alertElement, alertsList.firstChild);
        
        // Keep only last 20 alerts
        while (alertsList.children.length > 20) {
            alertsList.removeChild(alertsList.lastChild);
        }
        
        // Play notification sound
        this.playNotificationSound();
    }
    
    playNotificationSound() {
        // Optional: play a notification sound
        const audio = new Audio('/sounds/alert.mp3');
        audio.play().catch(e => console.log("Sound play failed:", e));
    }
}

// Usage
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    const alertsSystem = new SafeHorizonAlerts('alerts-dashboard', token);
});
```

---

## 🧪 Testing Your WebSocket

### Browser Console Testing

```javascript
// Step 1: Open browser console (F12)

// Step 2: Get your token (after login)
const token = localStorage.getItem('auth_token');
console.log("Token:", token ? "Found" : "Missing");

// Step 3: Create WebSocket
const ws = new WebSocket(`ws://localhost:8000/api/alerts/subscribe?token=${token}`);

// Step 4: Add event listeners
ws.onopen = () => console.log("✅ CONNECTED");
ws.onmessage = (e) => console.log("📨 MESSAGE:", e.data);
ws.onerror = (e) => console.error("❌ ERROR:", e);
ws.onclose = (e) => console.log("🔌 CLOSED:", e.code, e.reason);

// Step 5: Send heartbeat
ws.send("ping");

// Step 6: Check connection state
console.log("State:", ws.readyState); 
// 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED
```

### Test Alert Triggering

```javascript
// Trigger a test SOS alert from console
async function triggerTestAlert() {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch('http://localhost:8000/api/sos/trigger', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            latitude: 28.6139,
            longitude: 77.2090,
            message: "Test alert from frontend"
        })
    });
    
    const result = await response.json();
    console.log("Alert triggered:", result);
}

// Run in console
triggerTestAlert();
```

---

## 🏭 Production Best Practices

### 1. Environment Configuration

```javascript
// config.js
const config = {
    development: {
        apiUrl: 'http://localhost:8000',
        wsProtocol: 'ws:',
        wsHost: 'localhost:8000'
    },
    production: {
        apiUrl: 'https://api.safehorizon.com',
        wsProtocol: 'wss:',
        wsHost: 'api.safehorizon.com'
    }
};

const env = process.env.NODE_ENV || 'development';
export default config[env];

// Usage
import config from './config';

const wsUrl = `${config.wsProtocol}//${config.wsHost}/api/alerts/subscribe?token=${token}`;
```

### 2. Error Boundary (React)

```javascript
import React from 'react';

class WebSocketErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    
    componentDidCatch(error, errorInfo) {
        console.error("WebSocket error:", error, errorInfo);
        
        // Log to error tracking service
        // logErrorToService(error, errorInfo);
    }
    
    render() {
        if (this.state.hasError) {
            return (
                <div className="error-container">
                    <h2>Connection Error</h2>
                    <p>Unable to establish real-time connection</p>
                    <button onClick={() => window.location.reload()}>
                        Retry
                    </button>
                </div>
            );
        }
        
        return this.props.children;
    }
}
```

### 3. Logging and Monitoring

```javascript
class WebSocketLogger {
    static log(level, message, data = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            data,
            userAgent: navigator.userAgent
        };
        
        console.log(`[${level}] ${message}`, data);
        
        // Send to logging service
        this.sendToLoggingService(logEntry);
    }
    
    static sendToLoggingService(entry) {
        // Send to your logging service (e.g., Sentry, LogRocket)
        if (window.analytics) {
            window.analytics.track('WebSocket Event', entry);
        }
    }
}

// Usage in WebSocket handlers
ws.onopen = () => {
    WebSocketLogger.log('INFO', 'WebSocket connected');
};

ws.onerror = (error) => {
    WebSocketLogger.log('ERROR', 'WebSocket error', { error });
};
```

---

## 🔍 Debugging Tools

### Chrome DevTools Network Tab

1. Open DevTools (F12)
2. Go to **Network** tab
3. Filter by **WS** (WebSocket)
4. Look for:
   - **Status**: Should be "101 Switching Protocols"
   - **Messages**: Click connection to see all messages
   - **Frames**: See data sent/received
   - **Timing**: Connection establishment time

### WebSocket Test Tools

**Online Tools:**
- https://www.websocket.org/echo.html
- https://www.piesocket.com/websocket-tester

**Browser Extensions:**
- "Simple WebSocket Client" (Chrome)
- "WebSocket Test Client" (Firefox)

**Command Line:**
```bash
# Using wscat (Node.js)
npm install -g wscat
wscat -c "ws://localhost:8000/api/alerts/subscribe?token=YOUR_TOKEN"

# Using websocat
websocat "ws://localhost:8000/api/alerts/subscribe?token=YOUR_TOKEN"
```

### Logging Helper

```javascript
// Enhanced console logging for debugging
const DEBUG = true; // Set to false in production

const logger = {
    ws: (message, data) => {
        if (DEBUG) {
            console.log(`[WS] ${new Date().toLocaleTimeString()} - ${message}`, data || '');
        }
    },
    error: (message, error) => {
        console.error(`[WS ERROR] ${new Date().toLocaleTimeString()} - ${message}`, error);
    }
};

// Usage
ws.onopen = () => logger.ws('Connected');
ws.onmessage = (e) => logger.ws('Message received', e.data);
ws.onerror = (e) => logger.error('Error occurred', e);
```

---

## 📞 Support and Resources

### Common Issues Checklist

- [ ] Server is running (`http://localhost:8000/docs` should be accessible)
- [ ] You have a valid authentication token
- [ ] Token is passed in query parameter, not headers
- [ ] WebSocket URL uses `ws://` (or `wss://` for HTTPS)
- [ ] User has "authority" or "admin" role
- [ ] Token is not expired
- [ ] No CORS or firewall blocking
- [ ] Browser console shows no JavaScript errors

### API Endpoints for Testing

```javascript
// Test server is running
fetch('http://localhost:8000/docs')

// Test authentication
fetch('http://localhost:8000/api/auth/login-authority', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'authority@example.com',
        password: 'password123'
    })
})

// Test WebSocket (after login)
new WebSocket(`ws://localhost:8000/api/alerts/subscribe?token=${token}`)
```

### Quick Debug Script

```javascript
// Run this in browser console for complete diagnostic
async function diagnoseWebSocket() {
    console.log("🔍 SafeHorizon WebSocket Diagnostic");
    console.log("=" .repeat(50));
    
    // 1. Check token
    const token = localStorage.getItem('auth_token');
    console.log("1. Token:", token ? "✅ Found" : "❌ Missing");
    
    if (!token) {
        console.log("   ⚠️ Please login first");
        return;
    }
    
    // 2. Check token expiration
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expired = Date.now() > (payload.exp * 1000);
        console.log("2. Token expiry:", expired ? "❌ Expired" : "✅ Valid");
        console.log("   Role:", payload.role);
        console.log("   Email:", payload.email);
    } catch (e) {
        console.log("2. Token parse:", "❌ Failed", e.message);
    }
    
    // 3. Check server
    try {
        const response = await fetch('http://localhost:8000/docs');
        console.log("3. Server:", response.ok ? "✅ Running" : "❌ Error");
    } catch (e) {
        console.log("3. Server:", "❌ Not reachable", e.message);
    }
    
    // 4. Test WebSocket
    console.log("4. Testing WebSocket connection...");
    const wsUrl = `ws://localhost:8000/api/alerts/subscribe?token=${token}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log("   ✅ WebSocket connected successfully!");
        ws.close();
    };
    
    ws.onerror = (e) => {
        console.log("   ❌ WebSocket connection failed", e);
    };
    
    ws.onclose = (e) => {
        console.log("   Connection closed:", e.code, e.reason || "No reason");
    };
}

// Run diagnostic
diagnoseWebSocket();
```

---

## 🎓 Summary

**Key Points to Remember:**

1. ✅ **Token goes in query parameter**, not headers
2. ✅ **Use correct protocol**: `ws://` for HTTP, `wss://` for HTTPS
3. ✅ **Only authority/admin roles** can access WebSocket
4. ✅ **Implement heartbeat** (ping/pong every 30s)
5. ✅ **Handle reconnection** for non-auth errors
6. ✅ **Check token expiration** before connecting
7. ✅ **Parse messages carefully** with try/catch
8. ✅ **Monitor close codes** to understand disconnections

**Complete URL Format:**
```
ws://localhost:8000/api/alerts/subscribe?token=YOUR_JWT_TOKEN
```

**Need Help?**
- Check server logs for detailed error messages
- Use browser DevTools Network tab to inspect WebSocket frames
- Run the diagnostic script above to identify issues
- Verify authentication by testing other API endpoints first

---

Good luck with your integration! 🚀