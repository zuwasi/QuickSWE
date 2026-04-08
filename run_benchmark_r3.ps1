Set-Location "C:\Amp_demos\QuickSWE"
$logFile = "C:\Amp_demos\QuickSWE\benchmark_run3_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Write-Output "Starting run 3 at $(Get-Date)" | Tee-Object -FilePath $logFile
python multi_runner.py --runs 1 --agent deep3-vs-claude --timeout 600 2>&1 | Tee-Object -FilePath $logFile -Append
Write-Output "Run 3 finished at $(Get-Date)" | Tee-Object -FilePath $logFile -Append
