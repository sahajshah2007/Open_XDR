export default function ArchitectureFigure(){
  return <figure className="architecture-figure"><div className="architecture-scroll"><svg viewBox="0 0 1000 430" role="img" aria-label="TwinTrace architecture: sources to FastAPI, PostgreSQL and Redis/Celery, detections and investigations, simulated twin and reports">
    <defs><marker id="architecture-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#8caecc"/></marker></defs>
    <g fill="none" stroke="#8caecc" strokeWidth="1.5" markerEnd="url(#architecture-arrow)"><path d="M190 160 H245"/><path d="M435 160 H490"/><path d="M680 160 H735"/><path d="M835 210 V260 H335 V290"/><path d="M435 335 H490"/><path d="M585 210 V245 H845 V290" strokeDasharray="5 5"/></g>
    {[{x:20,y:70,w:170,h:180,title:'LOG SOURCES',body:['Wazuh · endpoints','Suricata · network alerts','Zeek · connections','Falco · runtime','Synthetic scenarios']},
      {x:245,y:105,w:190,h:105,title:'INGEST & NORMALIZE',body:['FastAPI / Pydantic','UTC + common fields']},
      {x:490,y:105,w:190,h:105,title:'STORE & DISPATCH',body:['PostgreSQL + outbox','Redis → Celery workers']},
      {x:735,y:105,w:220,h:105,title:'DETECT & CORRELATE',body:['Source alerts + enabled rules','Event links → investigations']},
      {x:490,y:290,w:190,h:95,title:'EVALUATE & EXPORT',body:['Ground truth / ATT&CK','HTML · JSON · CSV']},
      {x:245,y:290,w:190,h:95,title:'SIMULATE & VERIFY',body:['YAML response policies','Run-local state assertions']},
      {x:735,y:290,w:220,h:95,title:'DIGITAL TWIN',body:['Run-local model','Optional Neo4j projection']},
    ].map(box=><g key={box.title}><rect x={box.x} y={box.y} width={box.w} height={box.h} rx="10" fill="#142131" stroke="#39506a"/><text x={box.x+16} y={box.y+27} fill="#e8b45b" fontSize="11" fontFamily="monospace">{box.title}</text>{box.body.map((line,index)=><text key={line} x={box.x+16} y={box.y+52+index*23} fill="#b6c7da" fontSize="11">{line}</text>)}</g>)}
    <text x="20" y="385" fill="#7e94ae" fontSize="10">No real infrastructure effects</text>
    <text x="20" y="30" fill="#6d879e" fontSize="10" fontFamily="monospace" letterSpacing="2">TWINTRACE LAB / SYSTEM FIGURE</text>
  </svg></div><figcaption>Solid arrows show the processing path. The Neo4j branch is an additional projection; the local twin works without it.</figcaption></figure>;
}
