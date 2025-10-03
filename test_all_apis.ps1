# SafeHorizon API Test Script (PowerShell)
# Run all API endpoint tests using curl

$BASE_URL = "http://localhost:8000/api"
$HEALTH_URL = "http://localhost:8000/health"

# Color functions
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Failure { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ $msg" -ForegroundColor Cyan }
function Write-Header { param($msg) Write-Host "`n========== $msg ==========" -ForegroundColor Yellow }

# Test storage
$script:TOURIST_TOKEN = $null
$script:AUTHORITY_TOKEN = $null
$script:TOURIST_ID = $null
$script:AUTHORITY_ID = $null
$script:ALERT_ID = $null
$script:ZONE_ID = $null

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║      SafeHorizon API Test Suite (PowerShell)             ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Blue

# Test 1: Health Check
Write-Header "HEALTH CHECK"
try {
    $response = Invoke-RestMethod -Uri $HEALTH_URL -Method Get -ErrorAction Stop
    if ($response.status -eq "ok") {
        Write-Success "Health check passed"
    } else {
        Write-Failure "Health check failed"
    }
} catch {
    Write-Failure "Health check error: $($_.Exception.Message)"
    Write-Info "Make sure the server is running at $BASE_URL"
    exit 1
}

# Test 2: Register Tourist
Write-Header "AUTHENTICATION - TOURIST"
$timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$touristData = @{
    email = "test_tourist_$timestamp@example.com"
    password = "TestPass123!"
    name = "Test Tourist"
    phone_number = "+1234567890"
    nationality = "India"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/auth/register" -Method Post -Body $touristData -ContentType "application/json"
    $script:TOURIST_ID = $response.user_id
    Write-Success "Tourist registered: $($script:TOURIST_ID)"
} catch {
    Write-Failure "Tourist registration failed: $($_.Exception.Message)"
}

# Test 3: Login Tourist
$loginData = @{
    email = "test_tourist_$timestamp@example.com"
    password = "TestPass123!"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/auth/login" -Method Post -Body $loginData -ContentType "application/json"
    $script:TOURIST_TOKEN = $response.access_token
    Write-Success "Tourist logged in successfully"
} catch {
    Write-Failure "Tourist login failed: $($_.Exception.Message)"
}

# Test 4: Register Authority
Write-Header "AUTHENTICATION - AUTHORITY"
$authorityData = @{
    email = "test_authority_$timestamp@police.gov"
    password = "AuthPass123!"
    name = "Test Authority"
    badge_number = "BADGE$timestamp"
    department = "Test Police"
    rank = "Inspector"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/auth/register-authority" -Method Post -Body $authorityData -ContentType "application/json"
    $script:AUTHORITY_ID = $response.user_id
    Write-Success "Authority registered: $($script:AUTHORITY_ID)"
} catch {
    Write-Failure "Authority registration failed: $($_.Exception.Message)"
}

# Test 5: Login Authority
$authLoginData = @{
    email = "test_authority_$timestamp@police.gov"
    password = "AuthPass123!"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/auth/login-authority" -Method Post -Body $authLoginData -ContentType "application/json"
    $script:AUTHORITY_TOKEN = $response.access_token
    Write-Success "Authority logged in successfully"
} catch {
    Write-Failure "Authority login failed: $($_.Exception.Message)"
}

# Test 6: Start Trip
Write-Header "TRIP MANAGEMENT"
if ($script:TOURIST_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:TOURIST_TOKEN)" }
    $tripData = @{
        destination = "Mumbai, India"
        itinerary = "Visit Gateway of India"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/trip/start" -Method Post -Headers $headers -Body $tripData -ContentType "application/json"
        Write-Success "Trip started"
    } catch {
        Write-Failure "Trip start failed: $($_.Exception.Message)"
    }
}

# Test 7: Update Location
Write-Header "LOCATION SERVICES"
if ($script:TOURIST_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:TOURIST_TOKEN)" }
    $locationData = @{
        latitude = 19.0760
        longitude = 72.8777
        accuracy = 10.5
        altitude = 14.0
        speed = 5.2
        heading = 180.0
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/location/update" -Method Post -Headers $headers -Body $locationData -ContentType "application/json"
        Write-Success "Location updated"
    } catch {
        Write-Failure "Location update failed: $($_.Exception.Message)"
    }
    
    # Get Location History
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/location/history" -Method Get -Headers $headers
        Write-Success "Location history retrieved: $($response.count) locations"
    } catch {
        Write-Failure "Location history failed: $($_.Exception.Message)"
    }
}

# Test 8: Trigger SOS
Write-Header "SAFETY & ALERTS"
if ($script:TOURIST_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:TOURIST_TOKEN)" }
    $sosData = @{
        latitude = 19.0760
        longitude = 72.8777
        message = "Test Emergency"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/sos/trigger" -Method Post -Headers $headers -Body $sosData -ContentType "application/json"
        $script:ALERT_ID = $response.alert_id
        Write-Success "SOS triggered: Alert ID $($script:ALERT_ID)"
    } catch {
        Write-Failure "SOS trigger failed: $($_.Exception.Message)"
    }
    
    # Get Safety Score
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/safety/score" -Method Get -Headers $headers
        Write-Success "Safety score retrieved: $($response.safety_score)"
    } catch {
        Write-Failure "Safety score failed: $($_.Exception.Message)"
    }
}

# Test 9: Public Panic Alerts
Write-Header "PUBLIC APIs (No Auth)"
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/public/panic-alerts?limit=10" -Method Get
    Write-Success "Public panic alerts retrieved: $($response.total_alerts) alerts"
    Write-Info "Unresolved: $($response.unresolved_count), Resolved: $($response.resolved_count)"
} catch {
    Write-Failure "Public panic alerts failed: $($_.Exception.Message)"
}

# Test 10: Authority Monitoring
Write-Header "AUTHORITY MONITORING"
if ($script:AUTHORITY_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:AUTHORITY_TOKEN)" }
    
    # Get Active Tourists
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/tourists/active" -Method Get -Headers $headers
        Write-Success "Active tourists retrieved: $($response.count) tourists"
    } catch {
        Write-Failure "Active tourists failed: $($_.Exception.Message)"
    }
    
    # Get Recent Alerts
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/alerts/recent" -Method Get -Headers $headers
        Write-Success "Recent alerts retrieved"
    } catch {
        Write-Failure "Recent alerts failed: $($_.Exception.Message)"
    }
    
    # Get Heatmap Data
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/heatmap/data" -Method Get -Headers $headers
        Write-Success "Heatmap data retrieved"
    } catch {
        Write-Failure "Heatmap data failed: $($_.Exception.Message)"
    }
}

# Test 11: Alert Resolution
Write-Header "ALERT RESOLUTION"
if ($script:AUTHORITY_TOKEN -and $script:ALERT_ID) {
    $headers = @{ Authorization = "Bearer $($script:AUTHORITY_TOKEN)" }
    
    # Acknowledge Alert
    $ackData = @{ alert_id = $script:ALERT_ID } | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/incident/acknowledge" -Method Post -Headers $headers -Body $ackData -ContentType "application/json"
        Write-Success "Alert acknowledged"
    } catch {
        Write-Failure "Alert acknowledgment failed: $($_.Exception.Message)"
    }
    
    # Resolve Alert
    $resolveData = @{
        alert_id = $script:ALERT_ID
        resolution_notes = "Test resolution"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/authority/alert/resolve" -Method Post -Headers $headers -Body $resolveData -ContentType "application/json"
        Write-Success "Alert resolved"
    } catch {
        Write-Failure "Alert resolution failed: $($_.Exception.Message)"
    }
}

# Test 12: Zone Management
Write-Header "ZONE MANAGEMENT"
if ($script:AUTHORITY_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:AUTHORITY_TOKEN)" }
    $zoneData = @{
        name = "Test Zone"
        description = "Test restricted zone"
        zone_type = "restricted"
        coordinates = @(
            @(72.8777, 19.0760),
            @(72.8780, 19.0760),
            @(72.8780, 19.0763),
            @(72.8777, 19.0763),
            @(72.8777, 19.0760)
        )
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/zones/create" -Method Post -Headers $headers -Body $zoneData -ContentType "application/json"
        $script:ZONE_ID = $response.zone_id
        Write-Success "Zone created: $($script:ZONE_ID)"
    } catch {
        Write-Failure "Zone creation failed: $($_.Exception.Message)"
    }
}

# Test 13: Device Management
Write-Header "DEVICE MANAGEMENT"
if ($script:TOURIST_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:TOURIST_TOKEN)" }
    $deviceData = @{
        device_token = "test_device_$timestamp"
        device_type = "android"
        device_name = "Test Device"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/device/register" -Method Post -Headers $headers -Body $deviceData -ContentType "application/json"
        Write-Success "Device registered"
    } catch {
        Write-Failure "Device registration failed: $($_.Exception.Message)"
    }
    
    # List Devices
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/device/list" -Method Get -Headers $headers
        Write-Success "Devices listed: $($response.count) devices"
    } catch {
        Write-Failure "Device list failed: $($_.Exception.Message)"
    }
}

# Test 14: Broadcast System
Write-Header "BROADCAST SYSTEM"
if ($script:AUTHORITY_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:AUTHORITY_TOKEN)" }
    $broadcastData = @{
        title = "Test Broadcast"
        body = "This is a test broadcast"
        data = @{ test = "true" }
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/broadcast/all" -Method Post -Headers $headers -Body $broadcastData -ContentType "application/json"
        Write-Success "Broadcast sent to all users"
    } catch {
        Write-Failure "Broadcast failed: $($_.Exception.Message)"
    }
}

# Cleanup
Write-Header "CLEANUP"
if ($script:TOURIST_TOKEN) {
    $headers = @{ Authorization = "Bearer $($script:TOURIST_TOKEN)" }
    try {
        Invoke-RestMethod -Uri "$BASE_URL/trip/end" -Method Post -Headers $headers -ContentType "application/json" | Out-Null
        Write-Success "Trip ended"
    } catch {
        Write-Failure "Trip end failed: $($_.Exception.Message)"
    }
}

if ($script:AUTHORITY_TOKEN -and $script:ZONE_ID) {
    $headers = @{ Authorization = "Bearer $($script:AUTHORITY_TOKEN)" }
    try {
        Invoke-RestMethod -Uri "$BASE_URL/zones/$($script:ZONE_ID)" -Method Delete -Headers $headers | Out-Null
        Write-Success "Zone deleted"
    } catch {
        Write-Failure "Zone deletion failed: $($_.Exception.Message)"
    }
}

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║                    TEST SUMMARY                           ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Blue

Write-Info "Tourist ID: $script:TOURIST_ID"
Write-Info "Authority ID: $script:AUTHORITY_ID"
Write-Info "Alert ID: $script:ALERT_ID"
Write-Info "Zone ID: $script:ZONE_ID"

Write-Host "`n✓ All tests completed!`n" -ForegroundColor Green
