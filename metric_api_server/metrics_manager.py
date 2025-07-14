import numpy as np
import threading
from datetime import datetime
import requests
import logging

class MetricsCacheManager:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.__lock = threading.Lock()

        self._cache_timestamp = 0
        self._cache_matrix = []
        self._cache_dict = []
        self._refresh_cache() #throws exception
        self.metric_names = self._cache_matrix[0][1:].tolist() # all header row without switch id

    def get_metric(self, switch_id, metric_name):
        if metric_name not in self.metric_names:
            self.logger.warning(f"no metric by that name {metric_name}")
            raise ValueError(f"no metric by that name {metric_name}")
                 
        if self._is_cache_stale():
            #acquire lock to refresh
            if self._check_and_refresh_cache() is False:
                return None
    
        with self.__lock:
            if switch_id not in self._cache_dict:
                self.logger.warning(f"no switch by that id {switch_id}")
                raise ValueError(f"no switch by that id {switch_id}")
            return self._cache_dict[switch_id] #since the values are strings no need to make a thread-safe copy to return

            
            
    def list_metrics(self, names):
        if any(name not in self.metric_names for name in names):
            self.logger.warning(f"some metric names are invalid. names: {names}")
            raise ValueError(f"some metric names are invalid. names: {names}")
        
        indices_of_metric_columns = [self.metric_names.index(name) + 1 for name in names] #adding one because of missing "SwitchId" column
        
        if self._is_cache_stale():
            #acquire lock to refresh
            if self._check_and_refresh_cache() is False:
                return None
            
        with self.__lock:
            result = self._cache_matrix[:, [0] + indices_of_metric_columns].copy()
        
        return result
        

    def _is_cache_stale(self):
        return datetime.now().timestamp() - self._cache_timestamp > 10

    def _check_and_refresh_cache(self):
        with self.__lock:
            if self._is_cache_stale():
                try: 
                    self._refresh_cache()
                    return True
                except:
                    self.logger.exception(f"refreshing metrics failed") 
                    return False
            return True

    def _refresh_cache(self):
        self.logger.info("refreshing metrics")
        response = requests.get('http://localhost:9001/counters')
        response_received_time = datetime.now().timestamp()
        if response.status_code == 200:
            self._cache_timestamp = response_received_time
            data_lines = response.text.strip().splitlines()
            rows = [line.split(",") for line in data_lines]
            self._cache_matrix = np.array(rows, dtype=str)
            self._cache_dict = {row[0] : row[1:] for row in rows}
        else:
            self.logger.error(f"refreshing metrics failed. status:{response.status_code}, text:{response.text}")
            raise ConnectionError()
        