# Metrics Generation and Telemetry API

A Python Flask-based telemetry API server backed by a metrics data generator server. The system caches metrics data fetched periodically from an internal HTTP endpoint and exposes it via HTTP API with efficient thread-safe caching.

# Installation and running (on windows)

1. git clone the repo and open the folder in terminal
2. create a virtual environment

        python -m venv venv
3. activate the virtual environment

        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        .\venv\Scripts\Activate.ps1
4. install dependencies

        pip install flask numpy requests
5. run the data gen server

        python .\telemetry_server\app.py
6. to run the web api. open a new terminal window and repeat step #3 and then

        python .\metric_api_server\app.py

# Usage

The Data generator server (telemetry) has a single api method

a sample request to get its metrics:
        
    (Invoke-WebRequest 127.0.0.1:9001/counters).Content

The Web api server has two api methods:

1. sample request to get a single switch's metric by name

        (Invoke-WebRequest '127.0.0.1:8080/telemetry/GetMetric?switch=2&metric=Latency')

2. sample request to get a all switchs' specified metrics by name

        (Invoke-WebRequest '127.0.0.1:8080/telemetry/ListMetrics?metrics=BandwidthConsumption,CpuUsage,SuccessfulRequests').Content

3. also note I've included a test script to benchmark the system. test_concur_calls.ps1. simply run it after making sure the servers are up



# Design
## Assumptions
* there's no persistence between server runs. memory is wiped.
* metrics unit of measurement are known to all parties (can use just numbers)
* metric names can be used as strings and not as shared enums between server,generator and client
* at every "generation", all metrics generate value, so no need to handle cases where a metric value is missing
* all metrics names are fixed, no metric is removed or added, and their order remains the same

(I can ofcourse correct for all of these but would take a bit longer to implement)

## System Design
### Data generator (Telemetry)
from the assignment instructions I inferred that the system should generate a new set of metrics values every second.
I've implemented a randomizing function to initialize values for several metrics, add a randomized (but reasonable) step for that metric up or down, and a 0.01% chance of a spike in the data.

I've separated the server to two files:
metrics_generator - which handles the creation of metric matrix, initializing random initial values and stepping them every second.
app - which functions as a server "main" as well as controller. thus it handles setting up the server, and output logic - specifically, converting the metrics to csv code before returning to the "client".

in the comments to metrics_generator I specified that because of thread safety, I elected to create a copy of the metrics before returning it to the controller for converting. my reasoning is to preserve proper encapsulation and readability (more details in the comments) but it would only work for such a small dataset. if it grows larger I'd definitely need to pass a lambda that converts the csv in there.

although there's a second overall iteration over the matrix, api runtime is still in O(n\*m) territory. considering that conversion to csv cannot get lower then that I'm pretty much satisfied.
same goes for ther metrics generation runtime and memory - which are also at a *linear* O(n\*m)

### Web Api

from the assignment instructions I inferred that the freshness of metrics is tolareted at about 10 seconds.
so I resolved to implementing a 10 second on-demand cache.
seeing as the two api's have a different access to the data and the strong emphesis on fetch speed, I elected to implement the cache 2 ways:
1. the csv header row, to have a reference for all metric names and their position within the various caches.
2. GetMetric - a dictionary based cache, key is switch id and value is the rest of the CSV. search time is O(1) for the dictionary, O(n) for searching the index in the csv and O(1) to get to the value. overall runtime O(n). it could be improved by convering the csv line to a dictionary, don't think it would impact cache construction time sigificantly. I simply ran out of time before making the improvement. cache construction, about O(n\*m) for runtime and space

2. ListMetric - a 2d matrix that could be accessed via columns (as opposed to python's array of array default way of representing 2d arrays). search time is O(n\*m) with n being the number of metrics being queried, m being the overall number of metrics - to make a list of indeces to later make a sub matrix (there is an argument to be had about detecting when n is big enough that it's faster to search for the "missing" names instead. but aslong as m is small enough I don't think that's worth it here) and O(n\*l) with l number of rows (switchs) so overall runtime O(n\*m) + O(n\*l), and space complexity is O(n\*l). not sure it can be further optimized in a significant way.

both caches are thread safe. and both are linear O(n*m), so two don't have much of an impact
both employ a single lock just before refreshing the cache, and another single lock for accessing the cache.
cache #1 returns string values which are immutable so no threat of race condition after it's returned.
cache #2 returns a submatrix for the controller, which is by refernce, so a local copy had to be made before leaving the critical section.

there is an argument to be had about implementing a readers-writers dual lock system. but I found that for this specific use case, a single lock for 2 very small critical blocks was enough.

I've separated the server to two files:
metrics_manager - which handles the creation and refreshing of the cache, as well as supplying the underlying logic of extracting metrics.
app - which functions as a server "main" as well as controller. thus it handles setting up the server, and output logic - specifically, converting the metrics to csv code before returning to the "client" (It's nicer for debugging in the console and it didn't really add to the runtime since it's still linear)

## Design Tradeoffs, limits and improvements
    Double Iteration on Generator:
    as mentioned before, The generator internally processes the metrics data twice. if generated data grows larger we'll need to add a lambda function to remove one iteration at the cost of readibility

    Simple Locking in Web API:
    the single threading lock that locked the cache update in reads. for this use case it's working fine to assure concurrency but with heavier loads it must turn to readers writers lock

    cache refresh on demend:
    on the one hand, it means that a burst of requests will mostly be a cache hit, but the first request will suffer the latency of the refresh.
    on the other hand, a periodic refresh will mean that the cache is refreshed potentially for no reason.
    perhaps an interim solution - a halfway (5s) periodic refresh with a double buffer, so updates won't block readers (aside from an atomic reference swap) and the casche is always refreshed well before it's expiry

    no real orchestration of the servers:
    without careful ordering the server's run, the system can't run and not very fault tolerant at that angle.