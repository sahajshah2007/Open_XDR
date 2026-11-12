import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import requests
import json
import uuid
import time
from datetime import datetime

API_URL = "http://localhost:8000/api/v1/ingest/events"
HEADERS = {"x-api-key": os.environ["INGEST_API_KEY"]}

# We'll use a common IP and Host to trigger correlation
HOST_ID = "001-web-server"
IP_ADDRESS = "192.168.1.100" # Known malicious IP in our enrichment mock database

wazuh_event = {
    "source": "wazuh",
    "data": {
        "rule": {
            "id": "5710",
            "level": "8",
            "description": "sshd: Attempt to login using a non-existent user"
        },
        "agent": {
            "id": HOST_ID,
            "name": "web-server-01"
        },
        "data": {
            "srcip": IP_ADDRESS
        }
    }
}

suricata_event = {
    "source": "suricata",
    "data": {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "alert",
        "src_ip": IP_ADDRESS,
        "src_port": 45678,
        "dest_ip": "10.0.0.15",
        "dest_port": 22,
        "proto": "TCP",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 2010935,
            "rev": 3,
            "signature": "ET SCAN Suspicious inbound to SSH port 22",
            "category": "Attempted Information Leak",
            "severity": 2
        }
    }
}

zeek_event = {
    "source": "zeek",
    "data": {
        "ts": time.time(),
        "uid": "CHhAvVGS1DHFhG9y",
        "id.orig_h": IP_ADDRESS,
        "id.orig_p": 54321,
        "id.resp_h": "8.8.8.8",
        "id.resp_p": 53,
        "proto": "udp",
        "service": "dns_tunnel",
        "duration": 0.01,
        "query": "long-base64-encoded-string.malicious.com"
    }
}

apt_shell_event = {
    "source": "wazuh",
    "data": {
        "rule": {
            "id": "1002",
            "level": "10",
            "description": "Process Creation"
        },
        "agent": {
            "id": HOST_ID,
            "name": "web-server-01"
        },
        "data": {
            "Image": "/usr/bin/apt-get",
            "CommandLine": "apt-get -o APT::Update::Pre-Invoke::=bash update"
        }
    }
}

print("Sending Wazuh SSH Brute Force endpoint event...")
r1 = requests.post(API_URL, timeout=10, json=wazuh_event, headers=HEADERS)
print(f"Status: {r1.status_code}, Response: {r1.text}")

time.sleep(1)

print("\nSending Suricata Network Scan event (same Source IP)...")
r2 = requests.post(API_URL, timeout=10, json=suricata_event, headers=HEADERS)
print(f"Status: {r2.status_code}, Response: {r2.text}")

time.sleep(1)

print("\nSending Zeek DNS Tunneling event (same Source IP)...")
r3 = requests.post(API_URL, timeout=10, json=zeek_event, headers=HEADERS)
print(f"Status: {r3.status_code}, Response: {r3.text}")

time.sleep(1)

print("\nSending APT Shell Execution event (from SigmaHQ rule)...")
r4 = requests.post(API_URL, timeout=10, json=apt_shell_event, headers=HEADERS)
print(f"Status: {r4.status_code}, Response: {r4.text}")

print("\nSimulation complete. Check the UI at http://localhost:5173 to see the correlated incident!")
