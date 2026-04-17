import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

const NODES = [
  { id: 'surat',   name: 'AuroraTex Factory',  pos: [21.1702, 72.8311], role: 'Origin Factory',  risk: 15, color: '#16a34a' },
  { id: 'jnpt',    name: 'JNPT Port (Mumbai)',  pos: [18.9500, 72.9500], role: 'Primary Port',    risk: 12, color: '#16a34a' },
  { id: 'mundra',  name: 'Mundra Port',          pos: [22.8394, 69.7006], role: 'Alt Port (West)', risk: 8,  color: '#16a34a' },
  { id: 'delhi',   name: 'Delhi Distribution',   pos: [28.6139, 77.2090], role: 'Hub (North)',     risk: 10, color: '#16a34a' },
  { id: 'chennai', name: 'Chennai Port',          pos: [13.0827, 80.2707], role: 'Alt Port (East)', risk: 9,  color: '#16a34a' },
  { id: 'kolkata', name: 'Kolkata Hub',           pos: [22.5726, 88.3639], role: 'Hub (East)',      risk: 11, color: '#16a34a' },
];

const ROUTES = [
  { id: 'primary',  label: 'Primary Route',  pairs: [['surat','jnpt'],['jnpt','delhi'],['jnpt','kolkata']], color: '#2563eb', desc: 'Main export corridor via JNPT. Handles 80% of monthly container volume.' },
  { id: 'mundra',   label: 'Alt Route A',    pairs: [['surat','mundra'],['mundra','delhi']],                color: '#16a34a', desc: 'Western alternative via Mundra Port. +36 hrs, Rs. 1.8L extra cost.' },
  { id: 'chennai',  label: 'Alt Route B',    pairs: [['surat','chennai'],['chennai','kolkata']],            color: '#d97706', desc: 'Southern alternative via Chennai. +72 hrs, Rs. 3.2L extra cost.' },
];

const getNode = id => NODES.find(n => n.id === id);

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function RoutesPage() {
  return (
    <div style={{ height: '100%', display: 'flex', overflow: 'hidden' }}>

      {/* Left: map */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer center={[21,78]} zoom={5} style={{ height:'100%', width:'100%' }} zoomControl={false}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"/>

          {NODES.map(node => {
            const icon = L.divIcon({
              className: '',
              html: `<div style="
                width:14px;height:14px;border-radius:50%;
                background:${node.color};border:2px solid #080f1e;
                box-shadow:0 0 8px ${node.color};
              "></div>`,
              iconSize: [14,14], iconAnchor: [7,7]
            });
            return (
              <Marker key={node.id} position={node.pos} icon={icon}>
                <Popup>
                  <strong style={{fontSize:'14px'}}>{node.name}</strong><br/>
                  <span style={{fontSize:'12px',color:'#94a3b8'}}>{node.role}</span><br/>
                  <span style={{fontSize:'12px',color:'#4ade80'}}>Risk score: {node.risk} — STABLE</span>
                </Popup>
              </Marker>
            );
          })}

          {/* All routes shown at once */}
          {ROUTES.flatMap(route =>
            route.pairs.map(([a,b],i) => (
              <Polyline
                key={`${route.id}-${i}`}
                positions={[getNode(a).pos, getNode(b).pos]}
                pathOptions={{ color: route.color, weight: 2.5, opacity: 0.8 }}
              />
            ))
          )}
        </MapContainer>

        {/* Map legend */}
        <div style={{
          position:'absolute', bottom:'16px', left:'16px', zIndex:1000,
          background:'#080f1eee', border:'1px solid #1e3a5f',
          borderRadius:'8px', padding:'12px 16px'
        }}>
          {ROUTES.map(r => (
            <div key={r.id} style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'6px'}}>
              <div style={{width:'24px',height:'3px',background:r.color,borderRadius:'2px'}}/>
              <span style={{fontSize:'12px',color:'#94a3b8'}}>{r.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right: route + node details */}
      <div style={{
        width:'340px', flexShrink:0,
        background:'#080f1e', borderLeft:'1px solid #1e3a5f',
        padding:'20px', overflowY:'auto'
      }}>
        <div style={{fontSize:'11px',color:'#3b82f6',fontWeight:'700',letterSpacing:'2px',marginBottom:'6px',fontFamily:'JetBrains Mono,monospace'}}>
          ROUTE PLANNER
        </div>
        <h2 style={{fontSize:'20px',fontWeight:'700',color:'#f1f5f9',marginBottom:'20px'}}>
          All Supply Chain Routes
        </h2>

        {/* Routes */}
        {ROUTES.map(r => (
          <div key={r.id} style={{
            background:'#0d1829', border:`1px solid ${r.color}44`,
            borderLeft:`3px solid ${r.color}`,
            borderRadius:'8px', padding:'14px', marginBottom:'12px'
          }}>
            <div style={{fontSize:'14px',fontWeight:'600',color:'#f1f5f9',marginBottom:'6px'}}>{r.label}</div>
            <div style={{fontSize:'13px',color:'#64748b',lineHeight:'1.6',marginBottom:'10px'}}>{r.desc}</div>
            <div style={{display:'flex',gap:'6px',flexWrap:'wrap'}}>
              {r.pairs.map(([a,b],i) => (
                <span key={i} style={{
                  fontSize:'11px', padding:'2px 8px', borderRadius:'4px',
                  background:r.color+'18', color:r.color, border:`1px solid ${r.color}33`,
                  fontFamily:'JetBrains Mono,monospace'
                }}>
                  {getNode(a).name.split(' ')[0]} → {getNode(b).name.split(' ')[0]}
                </span>
              ))}
            </div>
          </div>
        ))}

        {/* Node list */}
        <div style={{fontSize:'11px',color:'#475569',textTransform:'uppercase',letterSpacing:'1px',margin:'20px 0 10px',fontFamily:'JetBrains Mono,monospace'}}>
          ALL NODES
        </div>
        {NODES.map(node => (
          <div key={node.id} style={{
            display:'flex',alignItems:'center',gap:'10px',
            padding:'10px', borderRadius:'6px',
            border:'1px solid #1e3a5f', marginBottom:'6px',
            background:'#0d1829'
          }}>
            <div style={{
              width:'10px',height:'10px',borderRadius:'50%',
              background:node.color,boxShadow:`0 0 5px ${node.color}`,flexShrink:0
            }}/>
            <div style={{flex:1}}>
              <div style={{fontSize:'13px',fontWeight:'500',color:'#f1f5f9'}}>{node.name}</div>
              <div style={{fontSize:'11px',color:'#475569'}}>{node.role}</div>
            </div>
            <div style={{
              fontSize:'11px',fontFamily:'JetBrains Mono,monospace',
              color:'#4ade80',fontWeight:'600'
            }}>
              {node.risk}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
