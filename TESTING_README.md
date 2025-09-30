# SafeHorizon API Testing Documentation

This directory contains comprehensive testing scripts for the SafeHorizon Tourist Safety Platform API.

## 📋 Available Test Scripts

### 1. **test_simple_api.py** - Simple Testing (Recommended)
- **Requirements**: Python 3.7+ (no external dependencies)
- **Features**: Tests all major endpoints with built-in libraries
- **Best for**: Quick testing, CI/CD, environments without external packages

### 2. **test_complete_api.py** - Advanced Testing
- **Requirements**: Python 3.7+ + httpx, websockets, rich
- **Features**: Beautiful output, WebSocket testing, real-time progress
- **Best for**: Development, detailed analysis, presentation demos

## 🚀 Quick Start

### Running the Simple Test Suite
```bash
# Test against local server (default)
python test_simple_api.py

# Test against custom server
python test_simple_api.py http://your-server.com:8000
```

### Running the Advanced Test Suite
```bash
# Install dependencies
pip install httpx websockets rich

# Run tests
python test_complete_api.py

# Custom server with verbose output
python test_complete_api.py --url http://your-server.com:8000 --verbose
```

## 📊 What Gets Tested

### 🔐 Authentication & Authorization
- ✅ Tourist registration and login
- ✅ Authority (police) registration and login
- ✅ Admin authentication
- ✅ Role-based access control
- ✅ JWT token validation

### 👤 Tourist Mobile App Endpoints
- ✅ `POST /auth/register` - Register new tourist
- ✅ `POST /auth/login` - Tourist login
- ✅ `GET /auth/me` - Get current user info
- ✅ `POST /trip/start` - Start tracking trip
- ✅ `POST /trip/end` - End current trip
- ✅ `GET /trip/history` - Get trip history
- ✅ `POST /location/update` - Update GPS location
- ✅ `GET /location/history` - Get location history
- ✅ `GET /safety/score` - Get AI safety score
- ✅ `POST /sos/trigger` - Emergency SOS alert

### 👮 Authority Dashboard Endpoints
- ✅ `POST /auth/register-authority` - Register police officer
- ✅ `POST /auth/login-authority` - Authority login
- ✅ `GET /tourists/active` - Get active tourists
- ✅ `GET /tourist/{id}/track` - Track specific tourist
- ✅ `GET /alerts/recent` - Get recent alerts
- ✅ `POST /incident/acknowledge` - Acknowledge incident
- ✅ `GET /zones/manage` - List safety zones
- ✅ `POST /zones/create` - Create restricted zone
- ✅ `DELETE /zones/{id}` - Delete zone

### 🤖 AI Service Endpoints
- ✅ `POST /ai/geofence/check` - Check location in zones
- ✅ `POST /ai/geofence/nearby` - Get nearby zones
- ✅ `POST /ai/anomaly/point` - Point anomaly detection
- ✅ `POST /ai/anomaly/sequence` - Sequence anomaly detection
- ✅ `POST /ai/score/compute` - Compute safety score
- ✅ `GET /ai/models/status` - AI models status

### 🔔 Notification Endpoints
- ✅ `POST /notify/sms` - Send SMS notification
- ✅ `GET /notify/history` - Notification history
- ✅ `GET /notify/settings` - Get notification settings

### ⚙️ Admin Endpoints
- ✅ `GET /system/status` - System health status
- ✅ `POST /system/retrain-model` - Retrain AI models
- ✅ `GET /users/list` - List all users
- ✅ `GET /analytics/dashboard` - Analytics data

### 🌐 Real-time Features (Advanced Test Only)
- ✅ WebSocket connection for live alerts
- ✅ Real-time alert broadcasting

## 📈 Sample Test Output

```
🚀 SAFEHORIZON API COMPREHENSIVE TEST SUITE
================================================================================
📅 Test Started: 2025-09-30 10:30:15
🌐 Server URL: http://localhost:8000
================================================================================

🏥 TESTING HEALTH ENDPOINT
========================================

============================================================
GET /health - PASS
============================================================
Response:
{
  "status": "ok"
}
============================================================

👤 TESTING TOURIST AUTHENTICATION
========================================

============================================================
POST /auth/register - PASS
============================================================
Response:
{
  "message": "Tourist registered successfully",
  "user_id": "abc123...",
  "email": "tourist_1696065015@test.com"
}
============================================================

... (continues for all endpoints)

🎯 SAFEHORIZON API TEST RESULTS SUMMARY
================================================================================

Test Results:
  ✅ Passed:  42
  ❌ Failed:  0
  ⏭️  Skipped: 0
  📊 Total:   42
  🎯 Success Rate: 100.0%

Endpoints Tested (42):
   1. GET /health
   2. POST /auth/register
   3. POST /auth/login
   4. GET /auth/me
   ... (full list)

================================================================================
🎉 ALL TESTS PASSED! SafeHorizon API is working correctly!
================================================================================
```

## 🔧 Test Configuration

### Environment Variables
The tests will automatically detect and use your server configuration. Make sure your server is running with:

```bash
# Start the SafeHorizon server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Test Data
The scripts automatically:
- ✅ Create test users with unique timestamps
- ✅ Generate realistic test data (locations, trips)
- ✅ Clean up created test data after completion
- ✅ Handle existing users gracefully

## 🛠️ Troubleshooting

### Common Issues

#### 1. Connection Refused
```bash
Error: [Errno 61] Connection refused
```
**Solution**: Make sure the SafeHorizon server is running on the specified port.

#### 2. Authentication Failures
```bash
Error: 401 Unauthorized
```
**Solution**: Check if user creation succeeded. The tests handle token management automatically.

#### 3. Database Errors
```bash
Error: 500 Internal Server Error
```
**Solution**: Ensure PostgreSQL is running and migrations are applied:
```bash
alembic upgrade head
```

#### 4. Missing Dependencies (Advanced Test)
```bash
ModuleNotFoundError: No module named 'httpx'
```
**Solution**: Install required packages:
```bash
pip install httpx websockets rich
```

### Debug Mode
For detailed debugging, check the server logs while running tests:

```bash
# Terminal 1: Start server with debug logs
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug

# Terminal 2: Run tests
python test_simple_api.py
```

## 📝 Test Customization

### Adding New Test Cases
To add new endpoint tests, modify the test scripts:

```python
def test_new_endpoint(self):
    """Test your new endpoint"""
    if "tourist" not in self.tokens:
        print("⚠️  Skipping test - no tourist token")
        return
    
    print("\n🆕 TESTING NEW ENDPOINT")
    print("="*40)
    
    data = {"key": "value"}
    status_code, response = self.make_request("POST", "/new/endpoint", 
                                            token=self.tokens["tourist"], 
                                            data=data)
    
    if status_code == 200:
        self.log_test("/new/endpoint", "POST", "PASS", response)
    else:
        self.log_test("/new/endpoint", "POST", "FAIL", response, 
                     f"New endpoint failed: {status_code}")
```

### Custom Assertions
Add specific validation logic:

```python
# Validate response structure
if status_code == 200:
    if "safety_score" in response and isinstance(response["safety_score"], int):
        self.log_test("/safety/score", "GET", "PASS", response)
    else:
        self.log_test("/safety/score", "GET", "FAIL", response, 
                     "Invalid response structure")
```

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Start PostgreSQL
      run: |
        sudo systemctl start postgresql
        sudo -u postgres createdb safehorizon_test
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run migrations
      run: alembic upgrade head
    
    - name: Start API server
      run: |
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 5
    
    - name: Run API tests
      run: python test_simple_api.py
```

## 📚 Additional Resources

- **API Documentation**: Check `API_ENDPOINTS.md` for detailed endpoint specifications
- **Server Setup**: See `README.md` for server installation and configuration
- **Database Schema**: Review `app/models/database_models.py` for data structures
- **Authentication**: Check `app/auth/` for authentication implementation details

## 🤝 Contributing

When adding new endpoints or features:
1. ✅ Add corresponding test cases to both test scripts
2. ✅ Update this documentation
3. ✅ Ensure all tests pass before submitting PR
4. ✅ Test with both simple and advanced test suites

---

**Happy Testing! 🎉**

For questions or issues, check the server logs and ensure all dependencies are correctly installed.