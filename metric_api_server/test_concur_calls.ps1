# Define the target URLs
$urls = @(
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests',
	'http://127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests'
)

# Store the jobs
$jobs = @()

# Start time
$start = Get-Date

# Launch all requests in background jobs
foreach ($url in $urls) {
    $jobs += Start-Job -ScriptBlock {
        param($u)
        Invoke-WebRequest -Uri $u
    } -ArgumentList $url
}

# Wait for all to complete
$jobs | ForEach-Object { $_ | Wait-Job }

# End time
$end = Get-Date

# Show total duration
Write-Host "`nTotal Time: $($end - $start)`n"

# Output results
foreach ($job in $jobs) {
    $result = Receive-Job $job
    Write-Host "Status Code: $($result.StatusCode), URL: $($result.BaseResponse.ResponseUri)"
    Remove-Job $job
}