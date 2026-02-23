Set-Location 'C:\Users\Firstz\Desktop\Task Management'
$proc = Start-Process -FilePath '.\venv\Scripts\python.exe' `
    -ArgumentList @('-X', 'utf8', 'main.py') `
    -PassThru `
    -RedirectStandardError 'err.txt' `
    -RedirectStandardOutput 'out.txt'

Start-Sleep -Seconds 7

if ($proc.HasExited) {
    Write-Host "Process exited with code: $($proc.ExitCode)"
    Write-Host "--- stdout ---"
    Get-Content out.txt -ErrorAction SilentlyContinue
    Write-Host "--- stderr ---"
    Get-Content err.txt -ErrorAction SilentlyContinue
} else {
    Write-Host "App running OK — PID: $($proc.Id)"
    Stop-Process -Id $proc.Id -Force
    Write-Host "Stopped for test"
    $err = Get-Content err.txt -ErrorAction SilentlyContinue
    if ($err) {
        Write-Host "--- stderr snippet ---"
        $err | Select-Object -First 15
    } else {
        Write-Host "No errors in stderr"
    }
}

Remove-Item out.txt, err.txt -ErrorAction SilentlyContinue
