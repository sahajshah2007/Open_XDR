"""Project the common event store into ACDT's optional Neo4j twin."""
from acdt.graph.client import GraphClient
from acdt.attack_engine.pathfinder import AttackEngine
from app.core.config import settings
from app.models.host import Host


def graph_client():
    return GraphClient(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)


def project_to_twin(db, event):
    client = graph_client()
    try:
        client.bootstrap()
        host = db.get(Host, event.host_id) if event.host_id else None
        if host:
            props = {"host_id": str(host.host_id), "criticality": host.criticality,
                     "last_seen": event.timestamp.isoformat()}
            ip = event.raw.get("agent", {}).get("ip") or event.raw.get("output_fields", {}).get("fd.lip")
            if ip:
                props["ip"] = ip
            client.upsert_host(host.host_name, **props)
            client.run("""MATCH (h:Host {hostname: $hostname})
                MERGE (a:DataAsset {id: $asset_id})
                SET a.critical = $critical, a.asset_value = $value
                MERGE (h)-[:HOSTS]->(a)""", hostname=host.host_name,
                asset_id=f"host:{host.host_id}", critical=host.criticality >= 8, value=host.criticality)
        src, dst = event.normalized.get("src_ip"), event.normalized.get("dst_ip")
        if src and dst:
            client.upsert_connection(src, dst)
        client.run("""MERGE (e:TelemetryEvent {event_id: $event_id})
            SET e.source = $source, e.event_type = $event_type, e.timestamp = $timestamp""",
            event_id=str(event.event_id), source=event.source,
            event_type=event.event_type, timestamp=event.timestamp.isoformat())
    finally:
        client.close()


def twin_snapshot():
    client = graph_client()
    try:
        nodes = client.run("""MATCH (h:Host) RETURN h.hostname AS id, h.hostname AS name,
            h.ip AS ip, h.criticality AS criticality LIMIT 200""")
        edges = client.run("""MATCH (a:Host)-[:CONNECTS_TO]->(b:Host)
            RETURN a.hostname AS source, b.hostname AS target LIMIT 500""")
        return {"nodes": nodes, "edges": edges, "limit": 200,
                "description": "Observed connectivity; paths do not establish exploitability."}
    finally:
        client.close()


def paths_to_critical(hostname):
    client = graph_client()
    try:
        return AttackEngine(client).shortest_path_to_critical(hostname)
    finally:
        client.close()


def local_snapshot(db):
    """A usable local connectivity model from recorded events; Neo4j is optional storage."""
    from app.models.event import Event
    nodes={};edges={};addresses={}
    for host in db.query(Host).limit(200):
        key=str(host.host_id)
        nodes[key]={'id':key,'name':host.host_name,'ip':None,'criticality':host.criticality,'kind':'host'}
    events=db.query(Event).order_by(Event.timestamp.desc()).limit(500).all()
    def scope(event):
        return event.raw.get('_lab',{}).get('run_id','imported')
    for event in events:
        host_ip=event.raw.get('agent',{}).get('ip') or event.raw.get('output_fields',{}).get('fd.sip')
        if host_ip and event.host_id and str(event.host_id) in nodes:
            addresses[(scope(event),host_ip)]=str(event.host_id);nodes[str(event.host_id)]['ip']=host_ip
    for event in events:
        src,dst=event.normalized.get('src_ip'),event.normalized.get('dst_ip')
        if not src or not dst: continue
        keys=[]
        for ip in [src,dst]:
            key=addresses.get((scope(event),ip),f'ip:{scope(event)}:{ip}')
            label=ip if scope(event)=='imported' else f'{ip} [{scope(event)[:8]}]'
            nodes.setdefault(key,{'id':key,'name':label,'ip':ip,'criticality':1,'kind':'address'})
            keys.append(key)
        edges[tuple(keys)]={'source':keys[0],'target':keys[1]}
    return {'nodes':list(nodes.values())[:200],'edges':list(edges.values())[:500],'limit':200,'backend':'local-simulation','description':'Local digital twin reconstructed from up to 500 recorded events. Connectivity does not establish exploitability.'}


def local_paths(db,hostname):
    graph=local_snapshot(db)
    start=next((node['id'] for node in graph['nodes'] if node['name']==hostname),None)
    targets={node['id'] for node in graph['nodes'] if (node['criticality'] or 1)>=8}
    names={node['id']:node['name'] for node in graph['nodes']}
    if start is None: return []
    queue=[(start,[start])];seen={start};paths=[]
    while queue and len(paths)<20:
        node,path=queue.pop(0)
        if node in targets:
            paths.append({'nodes':[names[item] for item in path],'hops':len(path)-1})
        if len(path)>10: continue
        for edge in graph['edges']:
            if edge['source']==node and edge['target'] not in seen and edge['target'] in names:
                seen.add(edge['target']);queue.append((edge['target'],path+[edge['target']]))
    return paths
