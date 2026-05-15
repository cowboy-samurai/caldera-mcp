#!/usr/bin/env python3
"""
Thin HTTP wrapper around the Caldera REST API v2.

Reads connection config from environment variables:
  CALDERA_URL        — base URL of the Caldera server (default: http://localhost:8888)
  CALDERA_API_KEY    — API key (red team key); must be set — raises ValueError if empty
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 30  # seconds for all Caldera API requests


class CalderaClient:
    def __init__(self):
        self.base_url = os.environ.get("CALDERA_URL", "http://localhost:8888").rstrip("/")
        api_key = os.environ.get("CALDERA_API_KEY", "")
        if not api_key:
            raise ValueError("CALDERA_API_KEY environment variable must be set")
        self.session = requests.Session()
        self.session.headers.update({
            "KEY": api_key,
            "Content-Type": "application/json",
        })

    def get(self, path: str, params: dict = None) -> dict | list:
        try:
            resp = self.session.get(f"{self.base_url}{path}", params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("Caldera GET %s failed: %s", path, e.response.status_code)
            raise RuntimeError(f"Caldera API error: {e.response.status_code}")
        return resp.json()

    def post(self, path: str, body: dict) -> dict | list:
        try:
            resp = self.session.post(f"{self.base_url}{path}", json=body, timeout=_TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("Caldera POST %s failed: %s", path, e.response.status_code)
            raise RuntimeError(f"Caldera API error: {e.response.status_code}")
        return resp.json()

    def patch(self, path: str, body: dict) -> dict:
        try:
            resp = self.session.patch(f"{self.base_url}{path}", json=body, timeout=_TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("Caldera PATCH %s failed: %s", path, e.response.status_code)
            raise RuntimeError(f"Caldera API error: {e.response.status_code}")
        return resp.json()

    def delete(self, path: str) -> str:
        try:
            resp = self.session.delete(f"{self.base_url}{path}", timeout=_TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("Caldera DELETE %s failed: %s", path, e.response.status_code)
            raise RuntimeError(f"Caldera API error: {e.response.status_code}")
        return "deleted"
