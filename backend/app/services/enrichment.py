"""Optional IP enrichment; provider outages never discard a detection."""
import ipaddress
import json
import logging
import requests
import redis
from app.core.config import settings
from app.services.configuration import read_setting

logger = logging.getLogger(__name__)


def enrich_alert(alert, db):
    key = read_setting(db, "otx_api_key", settings.OTX_API_KEY)
    if not key:
        alert.enrichment = {}
        return
    data = {}
    cache = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=0.5, socket_timeout=0.5)
    try:
        for ip in set(filter(None, [alert.source_ip, alert.destination_ip])):
            try:
                address = ipaddress.ip_address(ip)
                if not address.is_global:
                    continue
                cache_key = f"otx_cache:{ip}"
                try:
                    cached = cache.get(cache_key)
                except redis.RedisError:
                    cached = None
                if cached:
                    data[ip] = json.loads(cached)
                    continue
                family = "IPv4" if address.version == 4 else "IPv6"
                response = requests.get(f"https://otx.alienvault.com/api/v1/indicators/{family}/{ip}/general", headers={"X-OTX-API-KEY": key}, timeout=3)
                response.raise_for_status()
                payload = response.json()
                data[ip] = {"source": "AlienVault OTX", "pulse_count": payload.get("pulse_info", {}).get("count", 0), "reputation": payload.get("reputation", 0)}
                try:
                    cache.setex(cache_key, 86400, json.dumps(data[ip]))
                except redis.RedisError:
                    pass
            except (ValueError, requests.RequestException):
                logger.warning("Enrichment unavailable for %s", ip)
        alert.enrichment = data
    finally:
        cache.close()
