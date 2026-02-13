"""Collector: list, download, extract. See interface.py for contract."""

from powerbi_to_looker.collector.interface import CollectorProtocol
from powerbi_to_looker.collector.collector import Collector

__all__ = ["CollectorProtocol", "Collector"]
