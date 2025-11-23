$ErrorActionPreference = "Stop"

$version = "v1.9.4"
$url = "https://github.com/livekit/livekit/releases/download/$version/livekit_1.9.4_windows_amd64.zip"
$output = "livekit_server.zip"
$binDir = Join-Path $PSScriptRoot "bin"

# Create bin directory
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir | Out-Null
    Write-Host "Created bin directory at $binDir"
}

# Download
Write-Host "Downloading LiveKit Server $version..."
Invoke-WebRequest -Uri $url -OutFile $output

# Extract
Write-Host "Extracting..."
Expand-Archive -Path $output -DestinationPath $binDir -Force

# Cleanup
Remove-Item $output
Write-Host "LiveKit Server installed to $binDir"
Write-Host "You can now run ./start_app.ps1"
