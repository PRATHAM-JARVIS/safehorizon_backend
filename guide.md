# 🚀 SafeHorizon Frontend Developer Guide

A comprehensive guide for frontend developers to integrate with the SafeHorizon Tourist Safety Platform API.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication Flow](#authentication-flow)
3. [API Architecture](#api-architecture)
4. [Implementation Examples](#implementation-examples)
5. [Error Handling](#error-handling)
6. [Real-time Features](#real-time-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Base Configuration

```javascript
const API_BASE_URL = 'http://localhost:8000/api'; // Development
// const API_BASE_URL = 'https://your-domain.com/api'; // Production

const apiClient = {
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  
  // Add auth token to requests
  setAuthToken: (token) => {
    if (token) {
      apiClient.headers['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.headers['Authorization'];
    }
  }
};
```

### Installation Dependencies

```bash
# For React/React Native
npm install axios @react-native-async-storage/async-storage
# or
npm install fetch react-native-keychain

# For Vue.js
npm install axios vue-router

# For Angular
npm install @angular/common/http
```

---

## 🔐 Authentication Flow

### 1. Tourist Mobile App Authentication

#### Registration
```javascript
async function registerTourist(userData) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: userData.email,
        password: userData.password,
        name: userData.name,
        phone: userData.phone,
        emergency_contact: userData.emergencyContact,
        emergency_phone: userData.emergencyPhone
      })
    });

    const data = await response.json();
    
    if (response.ok) {
      console.log('Registration successful:', data);
      return { success: true, data };
    } else {
      throw new Error(data.detail || 'Registration failed');
    }
  } catch (error) {
    console.error('Registration error:', error);
    return { success: false, error: error.message };
  }
}
```

#### Login & Token Management
```javascript
class AuthService {
  constructor() {
    this.token = null;
    this.user = null;
  }

  async login(email, password) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok) {
        this.token = data.access_token;
        this.user = {
          id: data.user_id,
          email: data.email,
          role: data.role
        };

        // Store in secure storage
        await this.storeToken(this.token);
        await this.storeUser(this.user);
        
        // Set default auth header
        apiClient.setAuthToken(this.token);
        
        return { success: true, user: this.user };
      } else {
        throw new Error(data.detail || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  }

  async logout() {
    this.token = null;
    this.user = null;
    await this.clearStorage();
    delete apiClient.headers['Authorization'];
  }

  // Token storage (React Native example)
  async storeToken(token) {
    try {
      await AsyncStorage.setItem('auth_token', token);
    } catch (error) {
      console.error('Token storage error:', error);
    }
  }

  async getStoredToken() {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        this.token = token;
        apiClient.setAuthToken(token);
      }
      return token;
    } catch (error) {
      console.error('Token retrieval error:', error);
      return null;
    }
  }

  // Check if token is expired
  isTokenExpired() {
    if (!this.token) return true;
    
    try {
      const payload = JSON.parse(atob(this.token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp < currentTime;
    } catch (error) {
      return true;
    }
  }
}

const authService = new AuthService();
```

### 2. Authority Dashboard Authentication

```javascript
async function loginAuthority(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login-authority`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (response.ok) {
      // Store authority token
      localStorage.setItem('authority_token', data.access_token);
      localStorage.setItem('authority_user', JSON.stringify({
        id: data.user_id,
        email: data.email,
        role: data.role
      }));

      return { success: true, data };
    } else {
      throw new Error(data.detail || 'Authority login failed');
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

---

## 🏗️ API Architecture

### HTTP Client Setup

```javascript
class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: { ...this.defaultHeaders, ...options.headers },
      ...options
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, redirect to login
          await authService.logout();
          window.location.href = '/login';
          throw new Error('Session expired');
        }
        
        if (response.status === 403) {
          throw new Error('Access denied - insufficient permissions');
        }

        throw new Error(data.detail || `HTTP Error: ${response.status}`);
      }

      return { success: true, data };
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      return { success: false, error: error.message };
    }
  }

  // Authenticated requests
  async authenticatedRequest(endpoint, options = {}) {
    const token = authService.token || await authService.getStoredToken();
    
    if (!token || authService.isTokenExpired()) {
      throw new Error('No valid authentication token');
    }

    return this.request(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    });
  }
}

const apiClient = new APIClient(API_BASE_URL);
```

---

## 💡 Implementation Examples

### 1. Tourist Mobile App Features

#### Trip Management
```javascript
class TripService {
  async startTrip(destination, itinerary = null) {
    return await apiClient.authenticatedRequest('/trip/start', {
      method: 'POST',
      body: JSON.stringify({ destination, itinerary })
    });
  }

  async endTrip() {
    return await apiClient.authenticatedRequest('/trip/end', {
      method: 'POST'
    });
  }

  async getTripHistory() {
    return await apiClient.authenticatedRequest('/trip/history');
  }
}

// Usage Example
const tripService = new TripService();

// Start a trip
const startResult = await tripService.startTrip('Tokyo, Japan', 'Visit temples and museums');
if (startResult.success) {
  console.log('Trip started:', startResult.data.trip_id);
} else {
  console.error('Failed to start trip:', startResult.error);
}
```

#### Location Tracking
```javascript
class LocationService {
  constructor() {
    this.watchId = null;
    this.trackingInterval = 30000; // 30 seconds
  }

  async updateLocation(locationData) {
    return await apiClient.authenticatedRequest('/location/update', {
      method: 'POST',
      body: JSON.stringify({
        lat: locationData.latitude,
        lon: locationData.longitude,
        speed: locationData.speed,
        altitude: locationData.altitude,
        accuracy: locationData.accuracy,
        timestamp: new Date().toISOString()
      })
    });
  }

  // Start continuous location tracking
  startTracking() {
    if (navigator.geolocation) {
      this.watchId = navigator.geolocation.watchPosition(
        async (position) => {
          const result = await this.updateLocation(position.coords);
          if (result.success) {
            console.log('Location updated:', result.data);
            
            // Handle safety alerts
            if (result.data.safety_score < 50) {
              this.showSafetyAlert(result.data);
            }
          }
        },
        (error) => console.error('Location error:', error),
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    }
  }

  stopTracking() {
    if (this.watchId) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  showSafetyAlert(data) {
    // Show notification to user
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Safety Alert', {
        body: `Your safety score is ${data.safety_score}. Risk level: ${data.risk_level}`,
        icon: '/icons/warning.png'
      });
    }
  }
}
```

#### SOS Emergency System
```javascript
class EmergencyService {
  async triggerSOS(message, location, emergencyType = 'general') {
    return await apiClient.authenticatedRequest('/sos/trigger', {
      method: 'POST',
      body: JSON.stringify({
        message,
        location,
        emergency_type: emergencyType,
        contact_police: true,
        contact_family: true
      })
    });
  }

  // Quick SOS button
  async quickSOS() {
    // Get current location
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const result = await this.triggerSOS(
            'Emergency situation - immediate help needed!',
            {
              lat: position.coords.latitude,
              lon: position.coords.longitude
            }
          );
          resolve(result);
        },
        async () => {
          // Fallback without location
          const result = await this.triggerSOS(
            'Emergency situation - location unavailable',
            null
          );
          resolve(result);
        }
      );
    });
  }
}

// SOS Button Component (React Example)
function SOSButton() {
  const [isTriggering, setIsTriggering] = useState(false);
  const emergencyService = new EmergencyService();

  const handleSOS = async () => {
    setIsTriggering(true);
    const result = await emergencyService.quickSOS();
    
    if (result.success) {
      alert('SOS triggered! Help is on the way.');
    } else {
      alert('Failed to trigger SOS. Please try again.');
    }
    
    setIsTriggering(false);
  };

  return (
    <button 
      onClick={handleSOS}
      disabled={isTriggering}
      style={{
        backgroundColor: '#ff4444',
        color: 'white',
        padding: '20px',
        borderRadius: '50%',
        border: 'none',
        fontSize: '18px'
      }}
    >
      {isTriggering ? 'Sending...' : 'SOS'}
    </button>
  );
}
```

### 2. Authority Dashboard Features

#### Tourist Monitoring
```javascript
class AuthorityService {
  async getActiveTourists(limit = 50) {
    return await apiClient.authenticatedRequest(`/tourists/active?limit=${limit}`);
  }

  async trackTourist(touristId) {
    return await apiClient.authenticatedRequest(`/tourist/${touristId}/track`);
  }

  async getTouristAlerts(touristId) {
    return await apiClient.authenticatedRequest(`/tourist/${touristId}/alerts`);
  }

  async getRecentAlerts(limit = 20, severity = null) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (severity) params.append('severity', severity);
    
    return await apiClient.authenticatedRequest(`/alerts/recent?${params}`);
  }
}

// Dashboard Component (React Example)
function AuthorityDashboard() {
  const [tourists, setTourists] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const authorityService = new AuthorityService();

  useEffect(() => {
    loadDashboardData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    
    const [touristsResult, alertsResult] = await Promise.all([
      authorityService.getActiveTourists(),
      authorityService.getRecentAlerts()
    ]);

    if (touristsResult.success) {
      setTourists(touristsResult.data);
    }

    if (alertsResult.success) {
      setAlerts(alertsResult.data);
    }

    setLoading(false);
  };

  return (
    <div className="dashboard">
      <h1>Police Dashboard</h1>
      
      <div className="stats">
        <div className="stat-card">
          <h3>Active Tourists</h3>
          <p>{tourists.length}</p>
        </div>
        <div className="stat-card">
          <h3>Recent Alerts</h3>
          <p>{alerts.length}</p>
        </div>
      </div>

      <div className="alerts-section">
        <h2>Recent Alerts</h2>
        {alerts.map(alert => (
          <div key={alert.id} className={`alert alert-${alert.severity}`}>
            <h4>{alert.title}</h4>
            <p>{alert.description}</p>
            <small>{new Date(alert.created_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🔄 Real-time Features

### WebSocket Connection for Live Updates

```javascript
class WebSocketManager {
  constructor(url, token) {
    this.url = url;
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = new Map();
  }

  connect() {
    try {
      this.ws = new WebSocket(`${this.url}?token=${this.token}`);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  handleMessage(data) {
    const listeners = this.listeners.get(data.type) || [];
    listeners.forEach(callback => callback(data));
  }

  subscribe(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  unsubscribe(eventType, callback) {
    const listeners = this.listeners.get(eventType) || [];
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, 1000 * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage for Authority Dashboard
const wsManager = new WebSocketManager('ws://localhost:8000/api/alerts/subscribe', authToken);

// Subscribe to real-time alerts
wsManager.subscribe('safety_alert', (data) => {
  console.log('New safety alert:', data);
  showNotification(`Safety Alert: Tourist ${data.tourist_id} - Score: ${data.safety_score}`);
});

wsManager.subscribe('sos_alert', (data) => {
  console.log('SOS Alert:', data);
  showUrgentNotification(`🚨 SOS: ${data.tourist_name} needs immediate help!`);
});

wsManager.connect();
```

---

## ❌ Error Handling

### Comprehensive Error Handler
```javascript
class ErrorHandler {
  static handle(error, context = '') {
    console.error(`Error in ${context}:`, error);

    // Network errors
    if (error.name === 'NetworkError' || error.message.includes('fetch')) {
      return {
        type: 'network',
        message: 'Network connection error. Please check your internet connection.',
        action: 'retry'
      };
    }

    // Authentication errors
    if (error.message.includes('401') || error.message.includes('unauthorized')) {
      return {
        type: 'auth',
        message: 'Your session has expired. Please log in again.',
        action: 'login'
      };
    }

    // Permission errors
    if (error.message.includes('403') || error.message.includes('forbidden')) {
      return {
        type: 'permission',
        message: 'You do not have permission to perform this action.',
        action: 'none'
      };
    }

    // Validation errors
    if (error.message.includes('422') || error.message.includes('validation')) {
      return {
        type: 'validation',
        message: 'Please check your input and try again.',
        action: 'fix'
      };
    }

    // Server errors
    if (error.message.includes('500')) {
      return {
        type: 'server',
        message: 'Server error. Please try again later.',
        action: 'retry'
      };
    }

    // Generic error
    return {
      type: 'generic',
      message: error.message || 'An unexpected error occurred.',
      action: 'retry'
    };
  }

  static async handleWithRetry(apiCall, maxRetries = 3, delay = 1000) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await apiCall();
      } catch (error) {
        lastError = error;
        
        const errorInfo = this.handle(error, `Attempt ${attempt}`);
        
        if (errorInfo.action !== 'retry' || attempt === maxRetries) {
          throw error;
        }
        
        await new Promise(resolve => setTimeout(resolve, delay * attempt));
      }
    }
    
    throw lastError;
  }
}

// Usage Example
async function safeApiCall() {
  try {
    const result = await ErrorHandler.handleWithRetry(
      () => apiClient.authenticatedRequest('/safety/score'),
      3,
      1000
    );
    
    if (result.success) {
      return result.data;
    }
  } catch (error) {
    const errorInfo = ErrorHandler.handle(error, 'Safety Score');
    
    switch (errorInfo.action) {
      case 'login':
        // Redirect to login
        window.location.href = '/login';
        break;
      case 'retry':
        // Show retry button
        showRetryDialog(errorInfo.message);
        break;
      default:
        // Show error message
        showErrorMessage(errorInfo.message);
    }
  }
}
```

---

## ⚡ Best Practices

### 1. Token Management
```javascript
// Automatic token refresh
class TokenManager {
  static async refreshTokenIfNeeded() {
    const token = authService.token;
    if (!token) return false;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiresIn = payload.exp - Math.floor(Date.now() / 1000);
      
      // Refresh if token expires in less than 5 minutes
      if (expiresIn < 300) {
        await authService.refreshToken(); // Implement this method
        return true;
      }
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
    
    return false;
  }
}
```

### 2. Request Caching
```javascript
class CacheManager {
  constructor() {
    this.cache = new Map();
    this.ttl = 5 * 60 * 1000; // 5 minutes
  }

  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  clear() {
    this.cache.clear();
  }
}

const cache = new CacheManager();

// Cached API call
async function getCachedSafetyScore() {
  const cacheKey = 'safety_score';
  let data = cache.get(cacheKey);
  
  if (!data) {
    const result = await apiClient.authenticatedRequest('/safety/score');
    if (result.success) {
      data = result.data;
      cache.set(cacheKey, data);
    }
  }
  
  return data;
}
```

### 3. Offline Support
```javascript
class OfflineManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.pendingRequests = [];
    
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }

  handleOffline() {
    this.isOnline = false;
    console.log('App is now offline');
  }

  async handleOnline() {
    this.isOnline = true;
    console.log('App is back online');
    
    // Process pending requests
    while (this.pendingRequests.length > 0) {
      const request = this.pendingRequests.shift();
      try {
        await request();
      } catch (error) {
        console.error('Failed to process pending request:', error);
      }
    }
  }

  async queueRequest(requestFn) {
    if (this.isOnline) {
      return await requestFn();
    } else {
      this.pendingRequests.push(requestFn);
      throw new Error('Currently offline. Request queued for when connection is restored.');
    }
  }
}

const offlineManager = new OfflineManager();
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. 403 Forbidden Errors
```javascript
// Check token and role
function debugTokenIssues() {
  const token = authService.token;
  if (!token) {
    console.log('❌ No token found');
    return;
  }

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    console.log('Token payload:', payload);
    console.log('Role:', payload.role);
    console.log('Expires:', new Date(payload.exp * 1000));
    console.log('Is expired:', payload.exp < Math.floor(Date.now() / 1000));
  } catch (error) {
    console.log('❌ Invalid token format');
  }
}
```

#### 2. CORS Issues
```javascript
// Check if CORS is properly configured
function checkCORSSupport() {
  fetch(`${API_BASE_URL}/health`, {
    method: 'OPTIONS'
  })
  .then(response => {
    console.log('CORS preflight successful');
    console.log('Access-Control-Allow-Origin:', response.headers.get('Access-Control-Allow-Origin'));
  })
  .catch(error => {
    console.error('CORS issue detected:', error);
  });
}
```

#### 3. Network Connectivity
```javascript
function checkAPIConnectivity() {
  return fetch(`${API_BASE_URL}/health`)
    .then(response => {
      if (response.ok) {
        console.log('✅ API is reachable');
        return true;
      } else {
        console.log('❌ API returned error:', response.status);
        return false;
      }
    })
    .catch(error => {
      console.log('❌ Cannot reach API:', error.message);
      return false;
    });
}
```

### Debug Helper
```javascript
class APIDebugger {
  static enableDebugMode() {
    // Log all API requests
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
      console.log('🔍 API Request:', args[0], args[1]);
      return originalFetch.apply(this, args)
        .then(response => {
          console.log('📥 API Response:', response.status, response.statusText);
          return response;
        });
    };
  }

  static checkSystemStatus() {
    console.log('🔍 System Status Check:');
    console.log('- Online:', navigator.onLine);
    console.log('- Token:', authService.token ? '✅ Present' : '❌ Missing');
    console.log('- User:', authService.user);
    checkAPIConnectivity();
  }
}

// Enable in development
if (process.env.NODE_ENV === 'development') {
  APIDebugger.enableDebugMode();
}
```

---

## 🎯 Production Deployment Checklist

### Security
- [ ] Use HTTPS in production
- [ ] Implement proper token storage (Keychain/Keystore)
- [ ] Add request/response encryption for sensitive data
- [ ] Implement certificate pinning
- [ ] Add rate limiting handling

### Performance
- [ ] Implement request caching
- [ ] Add offline support
- [ ] Optimize bundle size
- [ ] Implement lazy loading
- [ ] Add performance monitoring

### Monitoring
- [ ] Add error tracking (Sentry, Bugsnag)
- [ ] Implement analytics
- [ ] Add crash reporting
- [ ] Monitor API performance
- [ ] Set up alerts for critical errors

---

## 📚 Additional Resources

- **API Documentation**: `/myapi.md`
- **Postman Collection**: Import from `/postman/SafeHorizon.json`
- **WebSocket Events**: Real-time event documentation
- **Error Codes**: Complete list of API error codes
- **Rate Limits**: API usage limits and best practices

---

## 🤝 Support

For technical support or questions:
- **Email**: dev-support@safehorizon.com
- **Slack**: #frontend-dev
- **Documentation**: https://docs.safehorizon.com

---

*Last updated: September 29, 2025*