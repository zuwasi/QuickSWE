Set-Location "C:\Amp_demos\QuickSWE"
$logFile = "C:\Amp_demos\QuickSWE\benchmark_run_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Write-Output "Starting benchmark at $(Get-Date)" | Tee-Object -FilePath $logFile
python multi_runner.py --runs 3 --agent deep3-vs-claude --timeout 600 2>&1 | Tee-Object -FilePath $logFile -Append
Write-Output "Benchmark finished at $(Get-Date)" | Tee-Object -FilePath $logFile -Append
