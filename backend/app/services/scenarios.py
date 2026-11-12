"""Deterministic synthetic fixtures, never executable attack commands."""
import random
from datetime import timedelta

TECHNIQUES = {
    'T1110': {'name':'Brute Force','tactic':'Credential access','url':'https://attack.mitre.org/techniques/T1110/'},
    'T1505.003': {'name':'Web Shell','tactic':'Persistence','url':'https://attack.mitre.org/techniques/T1505/003/'},
    'T1059.004': {'name':'Unix Shell','tactic':'Execution','url':'https://attack.mitre.org/techniques/T1059/004/'},
    'T1021.004': {'name':'SSH','tactic':'Lateral movement','url':'https://attack.mitre.org/techniques/T1021/004/'},
    'T1550.002': {'name':'Pass the Hash','tactic':'Defense evasion','url':'https://attack.mitre.org/techniques/T1550/002/'},
    'T1071.004': {'name':'DNS','tactic':'Command and control','url':'https://attack.mitre.org/techniques/T1071/004/'},
}

SCENARIOS = [
    {'id':'ssh-bruteforce','title':'SSH brute force','category':'Credential access','difficulty':'Introductory','duration':'45 virtual seconds','accent':'amber',
     'description':'Trace repeated authentication failures and study a simulated port block.','lesson':'See how repeated endpoint alerts become one investigation and a policy decision.','techniques':['T1110'],'sources':['wazuh','zeek']},
    {'id':'web-shell','title':'Web shell investigation','category':'Persistence & execution','difficulty':'Intermediate','duration':'75 virtual seconds','accent':'rose',
     'description':'Follow a network alert, a runtime web-shell observation, and shell execution.','lesson':'Compare source alerting with ATT&CK attribution and cross-source correlation.','techniques':['T1505.003','T1059.004'],'sources':['suricata','falco','wazuh']},
    {'id':'lateral-movement','title':'Lateral movement over SSH','category':'Lateral movement','difficulty':'Intermediate','duration':'90 virtual seconds','accent':'blue',
     'description':'Model a connection from a web asset toward a critical database asset.','lesson':'Explore the difference between observed connectivity and exploitability.','techniques':['T1021.004','T1059.004'],'sources':['zeek','falco','wazuh']},
    {'id':'credential-reuse','title':'Credential reuse','category':'Identity & defense policy','difficulty':'Advanced','duration':'60 virtual seconds','accent':'violet',
     'description':'Correlate alternate-authentication observations and simulate identity revocation.','lesson':'Inspect multi-source risk escalation and verify changes only in the simulation model.','techniques':['T1550.002'],'sources':['wazuh','falco']},
    {'id':'benign-maintenance','title':'Benign maintenance','category':'Negative control','difficulty':'Introductory','duration':'30 virtual seconds','accent':'mint',
     'description':'Replay ordinary web, DNS, and package-management activity.','lesson':'A working pipeline should not turn ordinary telemetry into an incident.','techniques':[],'sources':['zeek','wazuh']},
    {'id':'dns-detection-gap','title':'DNS detection gap','category':'Missed-detection study','difficulty':'Intermediate','duration':'40 virtual seconds','accent':'blue',
     'description':'Replay a labeled suspicious DNS fixture that the enabled rules do not detect.','lesson':'Observe a genuine false negative instead of inventing a successful detection.','techniques':['T1071.004'],'sources':['zeek']},
    {'id':'noisy-sensor','title':'Noisy sensor / false positive','category':'False-positive study','difficulty':'Introductory','duration':'20 virtual seconds','accent':'rose',
     'description':'An upstream sensor labels approved maintenance as suspicious.','lesson':'Use independent ground truth to expose a false positive in the source-alert pipeline.','techniques':[],'sources':['wazuh']},
]


def scenario_by_id(identifier):
    return next((dict(item,version=1) for item in SCENARIOS if item['id']==identifier),None)


def build_scenario(identifier,seed,run_id,start):
    scenario = scenario_by_id(identifier)
    if scenario is None:
        raise ValueError('Unknown scenario')
    rng=random.Random(seed)
    suffix=str(run_id).split('-')[0]
    octet=rng.randint(10,200)
    names={'web':f'web-{suffix}','db':f'db-{suffix}','client':f'client-{suffix}','identity':f'analyst-{suffix}'}
    ips={'web':f'192.0.2.{octet}','db':f'192.0.2.{octet+1}','client':f'198.51.100.{octet}','dns':'203.0.113.53'}
    nodes=[{'id':key,'name':name,'kind':key,'ip':ips.get(key),'criticality':9 if key=='db' else 4 if key=='web' else 1,'state':'active','blocked_ports':[]} for key,name in names.items()]
    topology={'nodes':nodes,'edges':[{'source':'client','target':'web','port':22,'label':'SSH','blocked':False},{'source':'web','target':'db','port':22,'label':'SSH','blocked':False}], 'provenance':'Scenario-defined topology; not a discovered production network.'}
    steps=[]
    def add(source,data,label,positive=False,techniques=None):
        data['_lab']={'run_id':str(run_id),'position':len(steps)}
        steps.append({'source':source,'data':data,'label':label,'expected_positive':positive,'expected_techniques':techniques or []})
    def when():
        return (start+timedelta(seconds=len(steps)*15)).isoformat()
    def wazuh(label,technique=None,asset='web',level=10,positive=True,tactic='execution',command=None):
        rule={'id':f'lab-{identifier}-{len(steps)}','level':level,'description':label}
        if technique: rule['mitre']={'id':[technique],'tactic':[tactic]}
        payload={'timestamp':when(),'rule':rule,'agent':{'id':f'{run_id}:{asset}','name':names[asset],'ip':ips[asset]},'data':{'srcip':ips['client'],'dstip':ips[asset],'srcuser':names['identity']}}
        if command: payload['data'].update(Image='/usr/bin/apt',CommandLine=command)
        add('wazuh',payload,label,positive,[technique] if positive and technique else [])
    def falco(label,technique,asset='web'):
        add('falco',{'time':when(),'hostname':names[asset],'rule':label,'priority':'Critical','tags':[technique],
                     'output_fields':{'proc.name':'sh','proc.cmdline':'[synthetic lab observation]','user.name':names['identity'],'fd.cip':ips['client'],'fd.sip':ips[asset]}},label,True,[technique])
    def zeek(label,service='http',source='client',target='web',positive=False,techniques=None):
        add('zeek',{'ts':(start+timedelta(seconds=len(steps)*15)).timestamp(),'uid':f'lab-{suffix}-{len(steps)}','id.orig_h':ips[source],'id.resp_h':ips[target],
                    'id.resp_p':53 if target=='dns' else 22 if service=='ssh' else 443,'service':service,'proto':'udp' if target=='dns' else 'tcp',
                    'query':'encoded-lab-sample.example.test' if positive else 'updates.example.test'},label,positive,techniques)
    if identifier=='ssh-bruteforce':
        zeek('SSH connection observed',service='ssh')
        for _ in range(3): wazuh('Synthetic failed SSH authentication','T1110',level=8,tactic='credential-access')
    elif identifier=='web-shell':
        add('suricata',{'timestamp':when(),'event_type':'alert','src_ip':ips['client'],'dest_ip':ips['web'], 'alert':{'signature_id':990001,'signature':'LAB suspicious web request','severity':2}},'Suspicious web request',True)
        falco('LAB web-shell runtime observation','T1505.003')
        wazuh('LAB shell execution','T1059.004')
    elif identifier=='lateral-movement':
        zeek('Web asset contacts database asset',service='ssh',source='web',target='db')
        falco('LAB remote SSH session','T1021.004','db')
        wazuh('LAB shell on database asset','T1059.004',asset='db')
    elif identifier=='credential-reuse':
        wazuh('LAB alternate authentication material','T1550.002',level=14,tactic='defense-evasion')
        falco('LAB credential reuse runtime observation','T1550.002')
    elif identifier=='benign-maintenance':
        zeek('Approved web connection')
        zeek('Routine DNS query',service='dns',source='web',target='dns')
        wazuh('Approved package metadata refresh',level=0,positive=False,command='apt update --print-uris')
    elif identifier=='dns-detection-gap':
        zeek('Labeled suspicious DNS channel',service='dns',source='web',target='dns',positive=True,techniques=['T1071.004'])
        zeek('Routine DNS comparison',service='dns',source='web',target='dns')
    elif identifier=='noisy-sensor':
        wazuh('LAB sensor flags an approved maintenance session',level=8,positive=False)
        zeek('Approved maintenance web request')
    snapshot={**scenario,'identity':names['identity'],'seed':seed,'fixture_events':len(steps),'ground_truth':'Independent event labels in the scenario fixture. Upstream alert records are not proof of real attacks.'}
    return snapshot,topology,steps
