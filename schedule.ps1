param([string]$At = '09:00')
$ErrorActionPreference = 'Stop'
$when = [datetime]::ParseExact($At, 'HH:mm', [Globalization.CultureInfo]::InvariantCulture)
$project = $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $project '.venv\financeiq-ready'))) {
    throw 'Run run.cmd verify successfully before registering the schedule.'
}
$name = 'FinanceIQ-Vega-Daily-ETL'
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
    throw "Task $name already exists. Remove it explicitly before replacing it."
}
$action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/d /s /c ""{0}\run.cmd" etl"' -f $project) -WorkingDirectory $project
$trigger = New-ScheduledTaskTrigger -Daily -At $when
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Import existing synthetic Vega CSVs into SQLite; no dashboard or regeneration.'
