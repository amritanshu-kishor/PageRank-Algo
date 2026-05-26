Set-Location -Path (Join-Path $PSScriptRoot "frontend")
..\venv\Scripts\python.exe -m http.server 8000
