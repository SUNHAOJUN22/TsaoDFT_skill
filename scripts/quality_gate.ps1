[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$Json,
    [ValidateRange(0, 86400)]
    [int]$TimeoutSeconds = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$QualityGate = Join-Path $RepositoryRoot "scripts\quality_gate.py"
if (-not (Test-Path -LiteralPath $QualityGate -PathType Leaf)) {
    throw "quality gate entry point is missing"
}

$PythonCommand = Get-Command -Name "python" -CommandType Application -ErrorAction Stop
$Arguments = [System.Collections.Generic.List[string]]::new()
$Arguments.Add($QualityGate)
if ($SkipTests.IsPresent) {
    $Arguments.Add("--skip-tests")
}
if ($Json.IsPresent) {
    $Arguments.Add("--json")
}
if ($TimeoutSeconds -gt 0) {
    $Arguments.Add("--timeout")
    $Arguments.Add([string]$TimeoutSeconds)
}

Push-Location -LiteralPath $RepositoryRoot
try {
    & $PythonCommand.Source @Arguments
    $ExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($null -eq $ExitCode) {
    $ExitCode = 1
}
exit [int]$ExitCode
