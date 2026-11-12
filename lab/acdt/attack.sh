#!/usr/bin/env bash
# Attacker playbook. Each invocation is one evaluation trial.
# Run INSIDE the attacker container on the isolated lab network only.
set -euo pipefail

TARGET_WEB="${TARGET_WEB:-web-01}"
LOG="${LOG:-/tmp/attack.log}"

log_event() {
  # Emit a synthetic attacker event as JSON for the telemetry pipeline.
  printf '{"time":"%s","attacker_ip":"%s","action":"%s","target":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(hostname -i 2>/dev/null || echo unknown)" "$1" "$2" \
    | tee -a "$LOG"
}

echo "[*] Scenario 1: SSH brute force"
log_event "brute_force" "$TARGET_WEB"
# hydra -L users.txt -P passwords.txt "ssh://${TARGET_WEB}" -t 4 -I || true

echo "[*] Scenario 2: SQL injection"
log_event "sqli" "$TARGET_WEB"
# curl "http://${TARGET_WEB}/login?user=admin'--&pass=x" || true

echo "[*] Scenario 3: port/service scan"
log_event "recon" "$TARGET_WEB"
# nmap -sV "$TARGET_WEB" || true

echo "[*] Attack trial complete. Events logged to ${LOG}"
