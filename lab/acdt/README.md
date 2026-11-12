# Optional ACDT laboratory

These original ACDT lab artifacts are kept outside the normal application stack.
The lab contains deliberately vulnerable services; it is never started by the root
Compose file. Its network is internal, and the example web port is bound to localhost.

From the project root, explicitly start it with:

```sh
docker compose -f lab/acdt/compose.yml up --build -d
```

`attack.sh` emits synthetic JSON trial events; the actual attack commands remain
commented out. Forward those records to the unified ingestion API using source
`attacker`. `otel-config.yaml` documents log collection and currently exports to
OTEL debug output; it does not provide a functioning Redis exporter or API bridge.
The mock cloud IAM service is an in-memory lab service, not a production integration.

The original graph-seeding script was not included because it deletes every graph
node. The merged platform builds its twin from stored telemetry instead.
