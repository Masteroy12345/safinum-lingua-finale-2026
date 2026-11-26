<#
.SYNOPSIS
  Enregistre votre URL publique (ngrok / cloudflared) auprès du sandbox SAFINUM pour les 3 canaux actifs.
.EXAMPLE
  .\register_endpoints.ps1 -TeamKey "sbx_votre_cle" -PublicUrl "https://xxxx.ngrok-free.app"
#>
param(
    [Parameter(Mandatory = $true)][string]$TeamKey,
    [Parameter(Mandatory = $true)][string]$PublicUrl
)

$base = $PublicUrl.TrimEnd('/')
$middlewareUrl = "$base/middleware"
$channels = @("ussd", "mobile", "web")

foreach ($ch in $channels) {
    $body = @{ channel = $ch; url = $middlewareUrl } | ConvertTo-Json
    Write-Host "Enregistrement du canal [$ch] -> $middlewareUrl ..."
    $resp = Invoke-RestMethod -Uri "https://www.safinum.cm/api/v1/sandbox/endpoint" `
        -Method Post `
        -Headers @{ "X-Team-Key" = $TeamKey; "Content-Type" = "application/json" } `
        -Body $body
    $resp | ConvertTo-Json -Depth 4
}

Write-Host "`nVerification de la configuration enregistree :"
Invoke-RestMethod -Uri "https://www.safinum.cm/api/v1/sandbox/endpoint" -Headers @{ "X-Team-Key" = $TeamKey } | ConvertTo-Json -Depth 4
