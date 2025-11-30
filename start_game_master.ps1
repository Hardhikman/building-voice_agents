$env:Path = "$PSScriptRoot\bin;$env:Path"
Write-Host "Starting LiveKit Server..."
Start-Process -FilePath "livekit-server" -ArgumentList "--dev"

Write-Host "Starting Backend (Game Master Agent)..."
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd backend; python -m uv run python src/agent_game_master.py dev"

Write-Host "Starting Frontend..."
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd frontend; pnpm dev"

Write-Host "All services are starting in separate windows."
Write-Host "Game Master Agent is running on port 8081"
