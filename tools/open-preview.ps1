$ErrorActionPreference = 'Stop'
$siteRoot = Split-Path -Parent $PSScriptRoot
$previewUrl = 'http://localhost:4181'
$response = $null
try { $response = Invoke-WebRequest -Uri $previewUrl -UseBasicParsing -TimeoutSec 2 } catch {}
if (-not $response) {
    $nodePath = (Get-Command node -ErrorAction Stop).Source
    Start-Process -FilePath $nodePath -ArgumentList @('tools/preview.mjs', '4181') -WorkingDirectory $siteRoot -WindowStyle Hidden
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 300
        try { $response = Invoke-WebRequest -Uri $previewUrl -UseBasicParsing -TimeoutSec 2; break } catch {}
    }
}
if (-not $response -or $response.Content -notmatch 'rd-hero') {
    throw 'The SWARM redesign preview did not start on port 4179.'
}
Start-Process $previewUrl
