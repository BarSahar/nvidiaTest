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

# Store the jobs and elapsed times
$jobs = @()
$timings = @()

# Launch all requests in background jobs with timing
foreach ($url in $urls) {
    $jobs += Start-Job -ScriptBlock {
        param($u)
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $u
        $sw.Stop()
        [PSCustomObject]@{
            Response = $response
            ElapsedMs = $sw.ElapsedMilliseconds
            Url = $u
        }
    } -ArgumentList $url
}

# Wait for all to complete
$jobs | ForEach-Object { $_ | Wait-Job }

# Collect results and print individual elapsed times
foreach ($job in $jobs) {
    $result = Receive-Job $job
    $timings += $result.ElapsedMs
    Write-Host ("URL: {0} | Status Code: {1} | Elapsed Time: {2} ms" -f $result.Url, $result.Response.StatusCode, $result.ElapsedMs)
    Remove-Job $job
}

# Calculate and show average elapsed time
$avg = ($timings | Measure-Object -Average).Average
Write-Host ("`nAverage elapsed time: {0:N2} ms" -f $avg)
