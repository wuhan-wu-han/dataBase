param([switch]$StopInfrastructure)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pidFile = Join-Path $projectRoot 'logs\full-service-pids.json'

if (Test-Path $pidFile) {
    $records = Get-Content $pidFile -Raw | ConvertFrom-Json
    foreach ($record in $records) {
        $process = Get-Process -Id ([int]$record.pid) -ErrorAction SilentlyContinue
        if (-not $process) { continue }
        $sameProcess = $process.StartTime.ToUniversalTime().Ticks.ToString() -eq [string]$record.startTimeTicks
        if ($sameProcess) {
            & taskkill.exe /PID $process.Id /T /F | Out-Null
            Write-Host "[STOP] $($record.name)" -ForegroundColor Green
        } else {
            Write-Warning "PID $($record.pid) belongs to another process and was not stopped."
        }
    }
    Remove-Item -LiteralPath $pidFile -Force
}

if ($StopInfrastructure) {
    & docker compose -f (Join-Path $projectRoot 'docker\docker-compose.yml') stop mysql redis zookeeper kafka
}

Write-Host 'Full service stopped.'

