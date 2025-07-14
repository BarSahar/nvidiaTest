from flask import Flask, request, Response
import logging
import sys
import csv
import io
from metrics_manager import MetricsCacheManager

app = Flask(__name__)
logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("webapi.log")
        ]
    )

#add master function to auth?
# add logs and metrics
# should I consider faults in the data? some metrics unavailable at times and how to tolerate it?

# the dictionary because of switch array. indeces because the List Metrics. both are extremely fast so I'll go with object because it's the most correct? or 2D array because it's less processing from the data gen
# assuming metrics are constant. no faults

# assuming metrics are changing every second
# assuming "freshness" is a 10 second window

@app.route("/")
def smoke_test():
    return ""

@app.route("/telemetry/GetMetric")
def get_metric():
    metric_name = request.args.get('metric')
    switch_id = request.args.get('switch')
    if metric_name is None or switch_id is None:
        logging.warning(f"missing arguments. metric_name:{metric_name}, switch_id:{switch_id}")
        return Response("missing arguments", status = 400)
    
    try: 
        val = metrics_cache.get_metric(switch_id, metric_name)
        if val is None:
            return Response("internal server error", status = 500)
        
        return Response(val, status = 200)
    
    except ValueError:
        return Response("illegal or unknown arguments", status = 400)

@app.route("/telemetry/ListMetrics")
def list_metrics():
    raw_metrics = request.args.get('metrics', '')
    metrics = raw_metrics.split(',') if raw_metrics else []
    if not metrics:
        logging.warning(f"missing arguments")
        return Response("missing arguments", status = 400)
    
    if len(metrics) != len(set(metrics)): #not discussed. the check adds to runtime but potentially user could duplicate the same argument 100 times and cripple the runtime.
        logging.warning(f"duplicate arguments")
        return Response("duplicate arguments", status = 400)
    
    try: 
        result = metrics_cache.list_metrics(metrics)
        if result is None:
            return Response("internal server error", status = 500)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(result)

        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=metrics.csv'
        return response
    
    except ValueError:
        logging.exception(f"illegal or unknown arguments in list_metrics")
        return Response("illegal or unknown arguments", status = 400)


if __name__ == '__main__':
    try: 
        setup_logging()
        metrics_cache = MetricsCacheManager()
        logger.info("Running api server")
        app.run(threaded=True, port=8080)

    except:
        logger.exception("metrics cache init failed")
        sys.exit(1)
