from flask import Flask, Response
from metrics_generator import MetricsDataGenerator
import csv
import io
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("telemetry.log")
        ]
    )


@app.route("/counters")
def get_counters():
    try:
        data =  metrics.get_metrics()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)

        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=metrics.csv'
        return response
    
    except Exception:
        logger.exception("get_counters failed, status 500")
        return Response("internal server error", status = 500)


if __name__ == '__main__':
    try:
        setup_logging()
        metrics = MetricsDataGenerator()
        logger.info("Running Telemtry server")
        app.run(port=9001)

    except:
        logger.exception("Unexpected exception in Telemtry server")
