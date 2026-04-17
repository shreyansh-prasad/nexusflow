import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useState, useCallback, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import AlertCard from '../components/AlertCard';
import ReroutePanel from '../components/ReroutePanel';
import Toast from '../components/Toast';
import ParticleBackground from '../components/ParticleBackground';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const NODES = [
  { id: 'surat',   name: 'AuroraTex Factory',  pos: [21.1702, 72.8311] },
  { id: 'jnpt',    name: 'JNPT Port (Mumbai)',  pos: [18.9500, 72.9500] },
  { id: 'mundra',  name: 'Mundra Port',          pos: [22.8394, 69.7006] },
  { id: 'delhi',   name: 'Delhi Distribution',   pos: [28.6139, 77.2090] },
  { id: 'chennai', name: 'Chennai Port',          pos: [13.0827, 80.2707] },
  { id: 'kolkata', name: 'Kolkata Hub',           pos: [22.5726, 88.3639] },
];

const NORMAL_ROUTES  = [['surat','jnpt'],['jnpt','delhi'],['jnpt','kolkata']];
const MUNDRA_REROUTE = [['surat','mundra'],['mundra','delhi']];
const CHENNAI_REROUTE= [['surat','chennai'],['chennai','kolkata']];

const GRAPH_DATA = {
  nodes: NODES.map(n => ({ id: n.id, name: n.name, val: 12 })),
  links: [
    { source:'surat',   target:'jnpt'    },
    { source:'jnpt',    target:'delhi'   },
    { source:'jnpt',    target:'kolkata' },
    { source:'surat',   target:'mundra'  },
    { source:'mundra',  target:'delhi'   },
    { source:'surat',   target:'chennai' },
    { source:'chennai', target:'kolkata' },
  ]
};

const MOCK_ALERTS = [
  {
    signalType:'weather', title:'Cyclone Warning — Mumbai', severity:4,
    description:'Severe weather approaching JNPT. Wind 85 km/h within 4 hrs.',
    exposure:'Rs. 2.3Cr', timeToImpact:'4 hrs', timeAgo:'Just now'
  },
  {
    signalType:'port', title:'Port Congestion Alert', severity:3,
    description:'JNPT at 94% capacity. Delays expected 18–36 hrs.',
    exposure:'Rs. 42L', timeToImpact:'18 hrs', timeAgo:'2 min ago'
  }
];

const CASCADE_PATH     = ['jnpt','surat','delhi','kolkata','mundra','chennai'];
const STABLE_SCORES    = { surat:15, jnpt:12, mundra:8,  delhi:10, chennai:9,  kolkata:11 };
const DISRUPTED_SCORES = { jnpt:89,  surat:58, delhi:47, kolkata:42, mundra:22, chennai:18 };

const nodeColor = s => s >= 70 ? '#dc2626' : s >= 40 ? '#d97706' : '#16a34a';
const getNode   = id => NODES.find(n => n.id === id);
const toPairs   = pairs => pairs.map(([a,b]) => [getNode(a).pos, getNode(b).pos]);

export default function DashboardPage() {
  const [disrupted,     setDisrupted]     = useState(false);
  const [cascading,     setCascading]     = useState(false);
  const [nodeScores,    setNodeScores]    = useState(STABLE_SCORES);
  const [animNode,      setAnimNode]      = useState(null);
  const [toast,         setToast]         = useState(null);
  const [scenario,      setScenario]      = useState(null);
  const [showMenu,      setShowMenu]      = useState(false);
  // FIX #1 — track which reroute is accepted so map updates
  const [acceptedRoute, setAcceptedRoute] = useState(null); // null | 'mundra' | 'chennai'
  const graphRef = useRef();

  const runCascade = useCallback(async (path, scores) => {
    setCascading(true);
    for (let i = 0; i < path.length; i++) {
      await new Promise(r => setTimeout(r, 520));
      setAnimNode(path[i]);
      setNodeScores(prev => ({ ...prev, [path[i]]: scores[path[i]] }));
    }
    await new Promise(r => setTimeout(r, 400));
    setAnimNode(null);
    setCascading(false);
  }, []);

  const triggerDisruption = (label) => {
    setShowMenu(false);
    setScenario(label);
    setDisrupted(true);
    setAcceptedRoute(null);
    runCascade(CASCADE_PATH, DISRUPTED_SCORES);
  };

  const resetAll = () => {
    setDisrupted(false); setScenario(null);
    setCascading(false); setAnimNode(null);
    setNodeScores(STABLE_SCORES); setAcceptedRoute(null);
  };

  // FIX #1 — when a route is accepted, update map lines + show toast
  const handleAcceptRoute = (route) => {
    setAcceptedRoute(route.id);
    setToast(
      `@VP_Supply_Chain: NexusFlow rerouted 3 shipments ${route.name}. ` +
      `Exposure reduced from Rs. 2.3Cr → Rs. 12L. ` +
      `Confirm with freight partner by 3 PM today.`
    );
  };

  // Decide which reroute lines to show on map
  const activeRerouteLines = acceptedRoute === 'mundra'
    ? MUNDRA_REROUTE
    : acceptedRoute === 'chennai'
      ? CHENNAI_REROUTE
      : (disrupted ? MUNDRA_REROUTE : []); // show mundra by default when disrupted but no selection yet

  const paintNode = useCallback((node, ctx, globalScale) => {
    const score = nodeScores[node.id] || 10;
    const color = nodeColor(score);
    const isAnim = animNode === node.id;
    const r = isAnim ? 9 : 6;
    if (isAnim) {
      ctx.beginPath(); ctx.arc(node.x, node.y, r+8, 0, 2*Math.PI);
      ctx.fillStyle = color+'33'; ctx.fill();
      ctx.beginPath(); ctx.arc(node.x, node.y, r+4, 0, 2*Math.PI);
      ctx.fillStyle = color+'22'; ctx.fill();
    }
    ctx.beginPath(); ctx.arc(node.x, node.y, r, 0, 2*Math.PI);
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#080f1e'; ctx.lineWidth = 2; ctx.stroke();
    const label = node.name.split(' ')[0];
    ctx.font = `${Math.max(8, 10/globalScale)}px Inter`;
    ctx.fillStyle = '#94a3b8'; ctx.textAlign = 'center';
    ctx.fillText(label, node.x, node.y + r + 11);
  }, [nodeScores, animNode]);

  const paintLink = useCallback((link, ctx) => {
    const src = link.source; const tgt = link.target;
    if (!src.x) return;
    const sId = typeof src==='object' ? src.id : src;
    const tId = typeof tgt==='object' ? tgt.id : tgt;
    const rerouteLinks = acceptedRoute === 'mundra'   ? MUNDRA_REROUTE
                       : acceptedRoute === 'chennai'  ? CHENNAI_REROUTE
                       : disrupted                    ? MUNDRA_REROUTE : [];
    const isReroute  = rerouteLinks.some(([a,b]) => (a===sId&&b===tId)||(b===sId&&a===tId));
    const isDisrupted= disrupted && NORMAL_ROUTES.some(([a,b]) => (a===sId&&b===tId)||(b===sId&&a===tId));
    ctx.beginPath(); ctx.moveTo(src.x, src.y); ctx.lineTo(tgt.x, tgt.y);
    ctx.strokeStyle = isReroute ? '#16a34a' : isDisrupted ? '#dc2626' : '#1d4ed8';
    ctx.lineWidth   = isReroute ? 2.5 : 1.5;
    ctx.globalAlpha = isReroute ? 0.9 : 0.6;
    ctx.stroke(); ctx.globalAlpha = 1;
  }, [disrupted, acceptedRoute]);

  // Stat numbers
  const stats = [
    { label:'Active Alerts',        value: disrupted ? '2' : '0',        color: disrupted?'#dc2626':'#16a34a', sub: disrupted?'2 high severity':'All clear' },
    { label:'Exposure at Risk',      value: disrupted ? 'Rs. 2.3Cr' : 'Rs. 0', color: disrupted?'#d97706':'#16a34a', sub: disrupted?'3 shipments':'No exposure' },
    { label:'Resilience Score',      value: disrupted ? '61' : '84',      color: disrupted?'#d97706':'#3b82f6', sub: disrupted?'↓ from 84':'Optimal' },
    { label:'Routes Rerouted',       value: disrupted ? '2' : '0',        color: disrupted?'#3b82f6':'#475569', sub: disrupted?'Mundra, Chennai':'None needed' },
  ];

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>

      {/* ── STAT BANNER ── */}
      <div style={{
        display:'flex', gap:'10px', padding:'10px 20px',
        background:'#080f1e', borderBottom:'1px solid #1e3a5f', flexShrink:0
      }}>
        {stats.map(s => (
          <div key={s.label} style={{
            flex:1, background:'#0d1829',
            border:`1px solid ${s.color}33`,
            borderTop:`2px solid ${s.color}88`,
            borderRadius:'8px', padding:'12px 16px',
            transition:'all 0.4s'
          }}>
            <div style={{ fontSize:'11px', color:'#475569', textTransform:'uppercase', letterSpacing:'0.8px', marginBottom:'6px', fontFamily:'JetBrains Mono,monospace' }}>
              {s.label}
            </div>
            <div style={{ fontSize:'22px', fontWeight:'700', color:s.color, fontFamily:'JetBrains Mono,monospace' }}>
              {s.value}
            </div>
            <div style={{ fontSize:'12px', color:'#475569', marginTop:'3px' }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* ── 3-PANEL BODY ── */}
      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>

        {/* LEFT PANEL */}
        <div style={{
          width:'300px', flexShrink:0,
          background:'#080f1e', borderRight:'1px solid #1e3a5f',
          padding:'14px', overflowY:'auto', display:'flex', flexDirection:'column', gap:'6px'
        }}>
          {/* Trigger button */}
          <div style={{ position:'relative', marginBottom:'8px' }}>
            <button
              onClick={() => !cascading && setShowMenu(v=>!v)}
              style={{
                width:'100%', padding:'11px 16px', borderRadius:'8px',
                background: disrupted ? '#1a0505' : '#0a1829',
                border:`1px solid ${disrupted?'#dc2626':'#1d4ed8'}`,
                color:'#fff', fontSize:'13px', fontWeight:'700',
                cursor: cascading ? 'not-allowed' : 'pointer', transition:'all 0.2s',
                letterSpacing:'0.5px', fontFamily:'JetBrains Mono,monospace'
              }}
            >
              {cascading ? '⏳  CASCADING...' : disrupted ? '🔴  DISRUPTION ACTIVE ▾' : '⚡  TRIGGER DISRUPTION ▾'}
            </button>

            {showMenu && !disrupted && (
              <div className="animate-fade-up" style={{
                position:'absolute', top:'calc(100% + 4px)', left:0, right:0, zIndex:100,
                background:'#0d1829', border:'1px solid #1e3a5f', borderRadius:'8px', overflow:'hidden'
              }}>
                {[
                  { label:'🌀  Cyclone Warning — Mumbai', id:'cyclone' },
                  { label:'⚓  Port Strike — JNPT',        id:'strike'  },
                  { label:'🌊  Red Sea Escalation',         id:'redsea'  },
                ].map((s,i) => (
                  <div key={s.id}
                    onClick={() => triggerDisruption(s.label)}
                    style={{
                      padding:'12px 14px', fontSize:'13px', cursor:'pointer',
                      borderBottom: i<2?'1px solid #1e3a5f':'none', color:'#cbd5e1',
                      transition:'background 0.15s'
                    }}
                    onMouseOver={e => e.currentTarget.style.background='#1e3a5f'}
                    onMouseOut={e =>  e.currentTarget.style.background='transparent'}
                  >
                    {s.label}
                  </div>
                ))}
              </div>
            )}

            {disrupted && !cascading && (
              <button onClick={resetAll} style={{
                width:'100%', marginTop:'6px', padding:'7px',
                borderRadius:'6px', background:'transparent',
                border:'1px solid #1e3a5f', color:'#475569',
                fontSize:'12px', cursor:'pointer', fontFamily:'JetBrains Mono,monospace'
              }}>
                ↺ Reset to stable
              </button>
            )}
          </div>

          {/* Scenario tag */}
          {scenario && (
            <div style={{
              background:'#0d1829', border:'1px solid #1e3a5f',
              borderRadius:'6px', padding:'7px 10px',
              fontSize:'11px', color:'#475569', marginBottom:'4px',
              fontFamily:'JetBrains Mono,monospace'
            }}>
              <span style={{color:'#fbbf24'}}>SCENARIO: </span>{scenario}
            </div>
          )}

          {/* Accepted route indicator */}
          {acceptedRoute && (
            <div style={{
              background:'#071a0f', border:'1px solid #16a34a44',
              borderLeft:'3px solid #16a34a', borderRadius:'6px',
              padding:'8px 10px', marginBottom:'4px', fontSize:'12px'
            }}>
              <span style={{color:'#4ade80', fontWeight:'600'}}>✅ Route active: </span>
              <span style={{color:'#94a3b8'}}>
                {acceptedRoute === 'mundra' ? 'Via Mundra Port' : 'Via Chennai Port'}
              </span>
              <div style={{fontSize:'11px', color:'#334155', marginTop:'3px'}}>
                Map updated — green lines show new route
              </div>
            </div>
          )}

          {/* Alert cards */}
          {disrupted
            ? MOCK_ALERTS.map((a,i) => <AlertCard key={i} alert={a} index={i}/>)
            : (
              <div style={{ textAlign:'center', padding:'40px 16px', color:'#334155' }}>
                <div style={{fontSize:'36px', marginBottom:'12px', opacity:0.4}}>✅</div>
                <div style={{color:'#475569', fontSize:'14px'}}>All nodes stable</div>
                <div style={{color:'#334155', marginTop:'6px', fontSize:'12px'}}>No active alerts</div>
              </div>
            )
          }

          {/* Reroute panel — passes acceptedRoute down */}
          <ReroutePanel
            visible={disrupted && !cascading}
            onAccept={handleAcceptRoute}
            acceptedRoute={acceptedRoute}
          />
        </div>

        {/* MAIN AREA */}
        <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>

          {/* MAP — top 58% */}
          <div style={{ flex:'0 0 58%', position:'relative' }}>
            <MapContainer center={[21,78]} zoom={5} style={{height:'100%',width:'100%'}} zoomControl={false}>
              <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"/>

              {NODES.map(node => {
                const score = nodeScores[node.id]||10;
                const color = nodeColor(score);
                const isAnim = animNode === node.id;
                const icon = L.divIcon({
                  className:'',
                  html:`<div style="
                    width:${isAnim?20:14}px;height:${isAnim?20:14}px;
                    border-radius:50%;background:${color};
                    border:2px solid #080f1e;
                    box-shadow:0 0 ${isAnim?18:6}px ${color};
                    transition:all 0.3s;
                  "></div>`,
                  iconSize:[20,20], iconAnchor:[10,10]
                });
                return (
                  <Marker key={node.id} position={node.pos} icon={icon}>
                    <Popup>
                      <div style={{fontFamily:'Inter,sans-serif'}}>
                        <strong style={{fontSize:'14px'}}>{node.name}</strong><br/>
                        <span style={{fontSize:'13px',color:'#94a3b8'}}>
                          Risk: {score} · {score>=70?'🔴 HIGH':score>=40?'🟡 MEDIUM':'🟢 STABLE'}
                        </span>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}

              {/* Ripple on JNPT when disrupted */}
              {disrupted && [1,2,3].map(i => (
                <Circle key={i} center={[18.95,72.95]} radius={i*65000}
                  pathOptions={{color:'#dc2626',fillOpacity:0,opacity:0.22/i,weight:1}}/>
              ))}

              {/* Normal routes — shown as red dashed when disrupted, blue when stable */}
              {toPairs(NORMAL_ROUTES).map((pos,i) => (
                <Polyline key={`n${i}`} positions={pos}
                  pathOptions={{
                    color: disrupted ? '#dc2626' : '#2563eb',
                    weight:2, opacity:0.8,
                    dashArray: disrupted ? '6 4' : undefined
                  }}/>
              ))}

              {/* FIX #1 — Active reroute lines (change based on accepted route) */}
              {disrupted && toPairs(activeRerouteLines).map((pos,i) => (
                <Polyline key={`r${i}`} positions={pos}
                  pathOptions={{color:'#16a34a',weight:3,dashArray:'9 5',opacity:0.95}}/>
              ))}
            </MapContainer>

            <div style={{
              position:'absolute', top:'10px', left:'10px', zIndex:1000,
              background:'#080f1ecc', border:'1px solid #1e3a5f',
              borderRadius:'6px', padding:'5px 12px',
              fontSize:'12px', color:'#475569', fontFamily:'JetBrains Mono,monospace'
            }}>
              LIVE MAP · 6 NODES · INDIA
              {acceptedRoute && (
                <span style={{color:'#4ade80', marginLeft:'8px'}}>
                  · {acceptedRoute==='mundra'?'MUNDRA ROUTE ACTIVE':'CHENNAI ROUTE ACTIVE'}
                </span>
              )}
            </div>
          </div>

          {/* FORCE GRAPH — bottom 42% */}
          <div style={{
            flex:'0 0 42%', background:'#060d1a',
            borderTop:'1px solid #1e3a5f',
            position:'relative', overflow:'hidden'
          }}>
            <ParticleBackground disrupted={disrupted}/>

            <div style={{
              position:'absolute', top:'8px', left:'10px', zIndex:10,
              fontSize:'12px', color:'#475569',
              background:'#080f1ecc', padding:'4px 12px',
              borderRadius:'5px', border:'1px solid #1e3a5f',
              fontFamily:'JetBrains Mono,monospace'
            }}>
              SUPPLY CHAIN GRAPH ·&nbsp;
              <span style={{color: cascading?'#fbbf24':disrupted?'#ef4444':'#4ade80'}}>
                {cascading?'CASCADE PROPAGATING':disrupted?'DISRUPTED':'STABLE'}
              </span>
            </div>

            <div style={{position:'relative',zIndex:1,width:'100%',height:'100%'}}>
              <ForceGraph2D
                ref={graphRef}
                graphData={GRAPH_DATA}
                nodeCanvasObject={paintNode}
                linkCanvasObject={paintLink}
                nodeCanvasObjectMode={() => 'replace'}
                linkCanvasObjectMode={() => 'replace'}
                backgroundColor="transparent"
                enableNodeDrag={false}
                enableZoomInteraction={false}
                cooldownTicks={100}
                nodeLabel="name"
              />
            </div>

            <div style={{
              position:'absolute', bottom:'10px', right:'12px', zIndex:10,
              display:'flex', gap:'14px', fontSize:'11px', color:'#475569',
              fontFamily:'JetBrains Mono,monospace'
            }}>
              {[['#16a34a','SAFE'],['#d97706','WARN'],['#dc2626','DANGER']].map(([c,l]) => (
                <div key={l} style={{display:'flex',alignItems:'center',gap:'5px'}}>
                  <div style={{width:'8px',height:'8px',borderRadius:'50%',background:c,boxShadow:`0 0 4px ${c}`}}/>
                  {l}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div style={{
          width:'260px', flexShrink:0,
          background:'#080f1e', borderLeft:'1px solid #1e3a5f',
          padding:'14px', overflowY:'auto'
        }}>
          {/* Weather */}
          <div style={{
            background:'#0d1829', border:'1px solid #1e3a5f',
            borderRadius:'10px', padding:'14px', marginBottom:'14px'
          }}>
            <div style={{fontSize:'11px',color:'#475569',textTransform:'uppercase',letterSpacing:'1px',marginBottom:'10px',fontFamily:'JetBrains Mono,monospace'}}>
              WEATHER · MUMBAI
            </div>
            <div style={{display:'flex',alignItems:'center',gap:'12px',marginBottom:'10px'}}>
              <span style={{fontSize:'32px'}}>{disrupted?'🌀':'☀️'}</span>
              <div>
                <div style={{fontSize:'24px',fontWeight:'700',fontFamily:'JetBrains Mono,monospace',color:'#f1f5f9'}}>
                  {disrupted?'29°C':'31°C'}
                </div>
                <div style={{fontSize:'13px',color:disrupted?'#ef4444':'#94a3b8',marginTop:'2px'}}>
                  {disrupted?'Cyclone Warning':'Clear skies'}
                </div>
              </div>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'6px'}}>
              {[
                {label:'Wind',     value:disrupted?'85 km/h NW':'12 km/h SW'},
                {label:'Humidity', value:disrupted?'94%':'68%'},
                {label:'Pressure', value:disrupted?'978 hPa ↓':'1012 hPa'},
                {label:'IMD Alert',value:disrupted?'RED':'NONE', danger:disrupted},
              ].map(w => (
                <div key={w.label} style={{background:'#080f1e',borderRadius:'5px',padding:'7px 8px'}}>
                  <div style={{fontSize:'10px',color:'#334155',marginBottom:'3px'}}>{w.label}</div>
                  <div style={{
                    fontSize:'12px',fontFamily:'JetBrains Mono,monospace',
                    color:w.danger?'#ef4444':'#94a3b8',fontWeight:w.danger?'700':'400'
                  }}>{w.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Insight */}
          <div style={{
            background:'#0a1829', border:'1px solid #1d4ed844',
            borderLeft:'3px solid #3b82f6', borderRadius:'8px', padding:'14px',
            marginBottom:'14px'
          }}>
            <div style={{fontSize:'11px',color:'#3b82f6',fontWeight:'700',marginBottom:'8px',letterSpacing:'1px',fontFamily:'JetBrains Mono,monospace'}}>
              🤖 AI INSIGHT
            </div>
            <div style={{fontSize:'13px',color:'#64748b',lineHeight:'1.7'}}>
              {disrupted
                ? 'Disruption detected via weather API + IMD bulletin. Cascade risk high across 4 nodes. Rerouting via Mundra reduces exposure by 82%.'
                : 'All 6 nodes nominal. Resilience score 84. No adverse weather, port congestion, or news signals in last 2 hrs.'
              }
            </div>
          </div>

          {/* Signal confidence */}
          <div style={{marginBottom:'14px'}}>
            <div style={{fontSize:'11px',color:'#475569',textTransform:'uppercase',letterSpacing:'1px',marginBottom:'10px',fontFamily:'JetBrains Mono,monospace'}}>
              SIGNAL CONFIDENCE
            </div>
            {[
              {label:'Weather API',        value:94, color:'#16a34a'},
              {label:'Port Authority Feed',value:88, color:'#16a34a'},
              {label:'News NLP',           value:76, color:'#d97706'},
              {label:'Shipping Registry',  value:61, color:'#d97706'},
            ].map(s => (
              <div key={s.label} style={{marginBottom:'10px'}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:'4px'}}>
                  <span style={{fontSize:'12px',color:'#94a3b8'}}>{s.label}</span>
                  <span style={{fontSize:'12px',fontFamily:'JetBrains Mono,monospace',color:s.color,fontWeight:'600'}}>{s.value}%</span>
                </div>
                <div style={{height:'3px',background:'#1e293b',borderRadius:'2px'}}>
                  <div style={{height:'100%',width:`${s.value}%`,background:s.color,borderRadius:'2px',boxShadow:`0 0 4px ${s.color}66`}}/>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Toast message={toast} onClose={() => setToast(null)}/>
    </div>
  );
}
