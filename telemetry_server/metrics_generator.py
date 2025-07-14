import uuid
import random
import threading
import time
from metrics_randomizer import MetricRandomizer
import logging


class MetricsDataGenerator:
    logger = logging.getLogger(__name__)
    _metric_headers = ["SwitchId", "BandwidthConsumption", "Latency", "CpuUsage", "FailedRequests", "SuccessfulRequests"]
    _num_of_switches = 5

    #stateless functions to initialize data and step it over time
    #assuming metrics units are known to both parties (Tal approves)
    _metric_rand_functions = [
        MetricRandomizer(   # BandwidthConsumption
            lambda : random.uniform(45.0, 55.0),
            lambda y: max(0, min(y + random.uniform(0.1, 1.5), 100))
        ),
        MetricRandomizer(   # Latency
            lambda : random.uniform(1.0, 10.0),
            lambda y: max(0, y + random.uniform(-1.1, 1.1))
        ),
        MetricRandomizer(   # CpuUsage
            lambda : random.uniform(45.0, 55.0),
            lambda y: max(0, min(y + random.uniform(-5.0, 5.0), 100))
        ),
        MetricRandomizer(   # FailedRequests
            lambda : random.randint(0, 2),
            lambda y: y +random.randint(0, 10)
        ),
        MetricRandomizer(   # SuccessfulRequests
            lambda : random.randint(1, 5),
            lambda y: y + random.randint(0, 20)
        )
    ]

    def __init__(self):
        self.__lock = threading.Lock()
        self._current_metrics_data = []
        self._init_metrics()
        self._schedule_task()
        
    def _init_metrics(self):
        try: 
            self._current_metrics_data.append(self._metric_headers)
            self.logger.info("initializing metrics")
            #switch_ids = [str(uuid.uuid4()) for _ in range(self._num_of_switches)]
            switch_ids = [i for i in range(self._num_of_switches)]
            with self.__lock:
                for switch_id in switch_ids:
                    self._current_metrics_data.append([switch_id] + [metric_func.init_value() for metric_func in self._metric_rand_functions])
            
        except Exception:
            self.logger.exception("metrics init failed")
            raise


    def _step_metrics(self):
        try: 
            self.logger.info("stepping metrics")
            with self.__lock:
                for i, metrics_row in enumerate(self._current_metrics_data):
                    if i == 0: #keep header line
                        continue
                    self._current_metrics_data[i] = [
                        metrics_row[0] # keep switch Id, take every metric value and apply it's corresponding random step logic
                        ] + [
                            metric_func.next(metric_value) for metric_func, metric_value in zip(self._metric_rand_functions, metrics_row[1:])
                        ]
                
        except Exception:
            self.logger.exception("step metrics failed")


    def get_metrics(self):
        # note: I'm not satisfied with the double iteration time (making a copy here and writing a csv in app.py) but it's a damned if you do
        # and damned if you don't situation. as far as I see there are 3 alternatives to save the second iteration time:
        # 1. get_metrics processes directly to csv - Breaking encapsulation from the controller side
        # 2. controller processes the data directly and not a copy by explicitly acquiring the lock - Breaking encapsulation of the inner class
        # 3. pass a conversion function as a parameter to get_metrics. best of both world but it impacts readability
        # 
        # Considering that the dataset is fairly small I'd preferred to leave it as is but should the iteration time be significantly longer, I'd choose #3
        try: 
            self.logger.info("get_metrics")
            with self.__lock:
                copied_data = [row[:] for row in self._current_metrics_data]
            return copied_data
        
        except Exception:
            self.logger.exception("get_metrics failed")


    def _schedule_task(self):
        def run_periodically():
            while True:
                try:
                    self._step_metrics()
                    time.sleep(1) # seconds

                except Exception:
                    self.logger.exception("Error in schedule_task thread")

        thread = threading.Thread(target=run_periodically, daemon=True)
        thread.start()