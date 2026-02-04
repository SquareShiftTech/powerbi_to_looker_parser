"""Collector stage: get Power BI data (API + .pbix or dict/path) into the pipeline."""

from powerbi_to_looker.collector.powerbi_collector import collect, collect_from_dict_or_path

__all__ = ["collect", "collect_from_dict_or_path"]
