$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = [IO.Path]::GetFullPath((Join-Path $taskRepo 'private/jirai-face-v3'))
$taskReceipt = Get-Content -LiteralPath (Join-Path $taskWork 'installation-receipt.json') -Raw | ConvertFrom-Json
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
if ($taskReceipt.target -ne $taskMods) { throw 'Unexpected MOD directory' }
$taskRecord = [IO.Path]::GetFullPath($taskReceipt.record)
if (!$taskRecord.StartsWith($taskWork + [IO.Path]::DirectorySeparatorChar)) { throw 'Backup outside Face3 workspace' }
function Assert-GameExited {
    if (@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count) { throw 'PBZ is running; exit before rollback.' }
}
function Assert-Hash($path, $hash) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) { throw "Missing or changed file: $path" }
}
Assert-GameExited
$taskCurrent = @(Get-ChildItem -LiteralPath $taskMods -File)
if ($taskCurrent.Count -ne @($taskReceipt.after).Count) { throw 'MOD set changed since installation' }
foreach ($item in $taskReceipt.after) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
$taskOld = @($taskReceipt.before | Where-Object { $_.name -in $taskReceipt.removed_face2 })
if ($taskOld.Count -ne 3 -or @($taskReceipt.added_face3).Count -ne 3) { throw 'Unexpected patch scope' }
foreach ($item in $taskOld) { Assert-Hash (Join-Path (Join-Path $taskRecord 'face2') $item.name) $item.sha256 }
$taskRetired = Join-Path $taskRecord 'face3-rolled-back'
if (Test-Path -LiteralPath $taskRetired) { throw 'Rollback already recorded' }
New-Item -ItemType Directory -Path $taskRetired | Out-Null
try {
    foreach ($name in $taskReceipt.added_face3) {
        Assert-GameExited
        Move-Item -LiteralPath (Join-Path $taskMods $name) -Destination (Join-Path $taskRetired $name)
    }
    foreach ($item in $taskOld) {
        Assert-GameExited
        [IO.File]::Copy((Join-Path (Join-Path $taskRecord 'face2') $item.name), (Join-Path $taskMods $item.name), $false)
        Assert-Hash (Join-Path $taskMods $item.name) $item.sha256
    }
    foreach ($item in $taskReceipt.before) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    [IO.File]::WriteAllText((Join-Path $taskRecord 'rollback.json'), (@{status='Face2 restored; R8 skirt and voice retained';time=[DateTimeOffset]::Now.ToString('o')} | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
    Write-Output 'FACE2_RESTORED_HASH_VERIFIED'
} catch {
    foreach ($item in $taskOld) {
        $path = Join-Path $taskMods $item.name
        if (Test-Path -LiteralPath $path) {
            Assert-Hash $path $item.sha256
            Move-Item -LiteralPath $path -Destination (Join-Path $taskRetired $item.name)
        }
    }
    foreach ($name in $taskReceipt.added_face3) {
        $path = Join-Path $taskRetired $name
        if (Test-Path -LiteralPath $path) { Move-Item -LiteralPath $path -Destination (Join-Path $taskMods $name) }
    }
    throw
}
