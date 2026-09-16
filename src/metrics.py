import time, logging
from typing import Dict, List, Any

logger = logging.getLogger('ObservabilityCore')

class InProcessPrometheusMetricsRegistry:
    def __init__(self):
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}

    def inc_counter(self, name: str, value: float = 1.0):
        self.counters[name] = self.counters.get(name, 0.0) + value
        logger.info('[METRICS-COUNTER] ' + str(name) + ' incremented by ' + str(value))

    def set_gauge(self, name: str, value: float):
        self.gauges[name] = value
        logger.info('[METRICS-GAUGE] ' + str(name) + ' set to ' + str(value))

    def observe_histogram(self, name: str, value: float):
        if name not in self.histograms: self.histograms[name] = []
        self.histograms[name].append(value)
        logger.info('[METRICS-HISTOGRAM] ' + str(name) + ' observed ' + str(value))

    def export_prometheus_text_format(self) -> str:
        lines = ['# HELP automotive_metrics In-Process Prometheus Metrics', '# TYPE automotive_metrics gauge']
        for k, v in self.counters.items(): lines.append('counter_' + str(k) + ' ' + str(v))
        for k, v in self.gauges.items(): lines.append('gauge_' + str(k) + ' ' + str(v))
        return chr(10).join(lines)

global_metrics = InProcessPrometheusMetricsRegistry()