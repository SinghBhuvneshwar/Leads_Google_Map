$ErrorActionPreference = "Stop"

$PythonCommand = $null

foreach ($Candidate in @("python", "py")) {
    $Command = Get-Command $Candidate -ErrorAction SilentlyContinue
    if ($Command) {
        try {
            if ($Candidate -eq "py") {
                & py -3 --version | Out-Null
                $PythonCommand = "py -3"
            } else {
                $VersionOutput = & python --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $VersionOutput -notmatch "Microsoft Store") {
                    $PythonCommand = "python"
                }
            }
        } catch {}
    }
    if ($PythonCommand) { break }
}

if (-not $PythonCommand) {
    Write-Host "Python was not found on PATH."
    Write-Host "Install Python 3.11+ from https://www.python.org/downloads/windows/"
    Write-Host "During install, tick: Add python.exe to PATH"
    Write-Host ""
    Write-Host "After installing Python, run INSTALL_AND_RUN.bat again."
    Read-Host "Press Enter to close"
    exit 1
}

if ($PythonCommand -eq "py -3") {
    & py -3 -m venv .venv
} else {
    & python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium

Write-Host ""
Write-Host "Setup complete. Start the app with:"
Write-Host ".\.venv\Scripts\Activate.ps1"
Write-Host "streamlit run app.py"
