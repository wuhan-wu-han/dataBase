param(
    [switch]$SkipInfrastructure,
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$logDir = Join-Path $projectRoot 'logs'
$pidFile = Join-Path $logDir 'full-service-pids.json'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

if (-not $env:RBAC_JWT_SECRET) {
    $env:RBAC_JWT_SECRET = 'change-this-rbac-secret-in-production'
    Write-Warning 'Using the development RBAC_JWT_SECRET. Set a strong random secret in production.'
}

# 企业实训默认使用本地短信记录器；如需真实邮件，请在启动前配置 SMTP_* 环境变量。
if (-not $env:NOTIFICATION_SMS_DEMO_MODE) { $env:NOTIFICATION_SMS_DEMO_MODE = 'true' }
if (-not $env:NOTIFICATION_AUTO_ENABLED) { $env:NOTIFICATION_AUTO_ENABLED = 'true' }
if (-not $env:PLATFORM_API_URL) { $env:PLATFORM_API_URL = 'http://127.0.0.1:8000' }

function Assert-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Test-Port([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        return $result.AsyncWaitHandle.WaitOne(300) -and $client.Connected
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

$started = @()
function Start-ManagedProcess {
    param([string]$Name, [int]$Port, [string]$FilePath, [string[]]$Arguments, [string]$WorkingDirectory)
    if (Test-Port $Port) {
        throw "$Name cannot start because port $Port is already in use. Stop the old service first."
    }
    $stdout = Join-Path $logDir "$Name.out.log"
    $stderr = Join-Path $logDir "$Name.err.log"
    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
    Start-Sleep -Milliseconds 500
    if ($process.HasExited) {
        throw "$Name failed to start. See $stderr"
    }
    $script:started += [pscustomobject]@{
        name = $Name
        pid = $process.Id
        startTimeTicks = $process.StartTime.ToUniversalTime().Ticks.ToString()
        port = $Port
    }
    Write-Host "[START] $Name - http://localhost:$Port" -ForegroundColor Green
}

Assert-Command python
Assert-Command java
Assert-Command mvn
Assert-Command npm.cmd

if (-not $SkipInfrastructure) {
    Assert-Command docker
    Write-Host '[START] MySQL, Redis, ZooKeeper and Kafka...' -ForegroundColor Cyan
    & docker compose -f (Join-Path $projectRoot 'docker\docker-compose.yml') up -d mysql redis zookeeper kafka
    if ($LASTEXITCODE -ne 0) { throw 'Docker infrastructure failed to start.' }
}

$platformPackages = @('fastapi', 'uvicorn', 'sqlalchemy', 'pandas', 'numpy')
foreach ($package in $platformPackages) {
    & python -c "import $package" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Missing Python package $package. Run: python -m pip install -r src/python/requirements.txt"
    }
}

$alarmJar = Join-Path $projectRoot 'alarm-warning-service\target\alarm-warning-service-1.0.0-SNAPSHOT.jar'
$gatewayJar = Join-Path $projectRoot 'api-gateway\target\api-gateway-1.0.0-SNAPSHOT.jar'
if ($Rebuild -or -not (Test-Path $alarmJar)) {
    & mvn -q -f (Join-Path $projectRoot 'alarm-warning-service\pom.xml') '-Dmaven.test.skip=true' package
    if ($LASTEXITCODE -ne 0) { throw 'Failed to build alarm-warning-service.' }
}
if ($Rebuild -or -not (Test-Path $gatewayJar)) {
    & mvn -q -f (Join-Path $projectRoot 'api-gateway\pom.xml') '-Dmaven.test.skip=true' package
    if ($LASTEXITCODE -ne 0) { throw 'Failed to build api-gateway.' }
}

Start-ManagedProcess 'platform' 8000 'python' @('-m','uvicorn','main:app','--host','0.0.0.0','--port','8000') (Join-Path $projectRoot 'src\python')
Start-ManagedProcess 'gas-asset' 8001 'python' @('main.py') (Join-Path $projectRoot 'gas_asset_manage')
Start-ManagedProcess 'road-hazard' 8002 'python' @('main.py') (Join-Path $projectRoot 'road_hazard_control')
Start-ManagedProcess 'gas-risk' 8003 'python' @('main.py') (Join-Path $projectRoot 'gas_risk_control')
Start-ManagedProcess 'water-supply' 8004 'python' @('main.py') (Join-Path $projectRoot 'water_supply_control')
Start-ManagedProcess 'manhole-cover' 8005 'python' @('main.py') (Join-Path $projectRoot 'manhole_cover_control')
Start-ManagedProcess 'alarm-warning' 8085 'java' @('-jar', $alarmJar) (Join-Path $projectRoot 'alarm-warning-service')
Start-ManagedProcess 'api-gateway' 8080 'java' @('-jar', $gatewayJar) (Join-Path $projectRoot 'api-gateway')
Start-ManagedProcess 'frontend' 5173 'npm.cmd' @('run','dev','--','--host','0.0.0.0') (Join-Path $projectRoot 'alarm-warning-frontend')

$started | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8

Write-Host 'Waiting for the gateway and authentication service...' -ForegroundColor Cyan
$loginOk = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    try {
        $body = @{ username = 'admin'; password = 'Admin@123' } | ConvertTo-Json
        $response = Invoke-RestMethod -Method Post -Uri 'http://localhost:8080/api/platform/auth/login' `
            -ContentType 'application/json' -Body $body -TimeoutSec 3
        if ($response.accessToken) { $loginOk = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}

if (-not $loginOk) {
    Write-Warning "Processes started but the login smoke test failed. Check logs in $logDir."
    exit 1
}

Write-Host ''
Write-Host 'Full service is ready: http://localhost:5173/login' -ForegroundColor Green
Write-Host 'Default administrator: admin / Admin@123'
Write-Host 'Services: platform 8000, assets 8001, road 8002, gas 8003, water 8004, manhole 8005, gateway 8080, alert 8085'
Write-Host 'Stop: powershell -ExecutionPolicy Bypass -File scripts/stop_full_service.ps1'

