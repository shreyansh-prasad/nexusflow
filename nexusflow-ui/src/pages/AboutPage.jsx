export default function AboutPage({ onNavigate }) {
  return (
    <div style={{ height: '100%', overflowY: 'auto', background: '#080f1e', padding: '40px 60px' }}>
      <div style={{ maxWidth: '860px', margin: '0 auto' }}>

        {/* Hero */}
        <div style={{
          background: 'linear-gradient(135deg, #0d1f3c, #0a1829)',
          border: '1px solid #1e3a5f', borderRadius: '16px',
          padding: '40px', marginBottom: '32px', position: 'relative', overflow: 'hidden'
        }}>
          {/* Background hex decoration */}
          <svg style={{ position:'absolute', right:'-20px', top:'-20px', opacity:0.06 }} width="200" height="200" viewBox="0 0 36 36">
            <polygon points="18,2 31,9.5 31,26.5 18,34 5,26.5 5,9.5" fill="none" stroke="#3b82f6" strokeWidth="1"/>
          </svg>

          <div style={{ fontSize:'11px', color:'#3b82f6', fontWeight:'700', letterSpacing:'2px', marginBottom:'12px', fontFamily:'JetBrains Mono,monospace' }}>
            ABOUT NEXUSFLOW™
          </div>
          <h1 style={{ fontSize:'32px', fontWeight:'800', color:'#f1f5f9', marginBottom:'16px', letterSpacing:'-0.5px' }}>
            Predictive Supply Chain Intelligence
          </h1>
          <p style={{ fontSize:'15px', color:'#64748b', lineHeight:'1.8', maxWidth:'600px' }}>
            NexusFlow is built for exporters like AuroraTex Industries who can't afford to react slowly. We detect disruptions before they happen, calculate rerouting options in seconds, and let managers take action with a single click.
          </p>

          <button
            onClick={() => onNavigate('dashboard')}
            style={{
              marginTop: '24px', padding: '12px 28px',
              borderRadius: '8px', background: '#1d4ed8',
              border: '1px solid #3b82f6', color: '#fff',
              fontSize: '14px', fontWeight: '700', cursor: 'pointer',
              transition: 'all 0.2s', fontFamily: 'JetBrains Mono, monospace',
              letterSpacing: '0.5px'
            }}
            onMouseOver={e => e.currentTarget.style.background = '#2563eb'}
            onMouseOut={e =>  e.currentTarget.style.background = '#1d4ed8'}
          >
            ⚡ Open Live Dashboard
          </button>
        </div>

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '32px' }}>
          {[
            { value: '< 90s', label: 'Detection to action',   color: '#3b82f6' },
            { value: '82%',   label: 'Risk reduction (avg)',   color: '#16a34a' },
            { value: '6',     label: 'Supply chain nodes',     color: '#8b5cf6' },
            { value: '24/7',  label: 'Monitoring uptime',      color: '#d97706' },
          ].map(s => (
            <div key={s.label} style={{
              background: '#0d1829', border: `1px solid ${s.color}33`,
              borderTop: `3px solid ${s.color}`,
              borderRadius: '10px', padding: '20px 16px', textAlign: 'center'
            }}>
              <div style={{ fontSize: '28px', fontWeight: '800', color: s.color, fontFamily: 'JetBrains Mono, monospace', marginBottom: '6px' }}>
                {s.value}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Two column: The problem + The solution */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '32px' }}>
          <div style={{
            background: '#0d1829', border: '1px solid #dc262633',
            borderRadius: '12px', padding: '24px'
          }}>
            <div style={{ fontSize: '18px', marginBottom: '12px' }}>❌</div>
            <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f1f5f9', marginBottom: '10px' }}>
              Without NexusFlow
            </h3>
            {[
              'Manager reads about cyclone on news — 2 hrs late',
              'Manually calls freight partners — another 1 hr',
              'No visibility into financial exposure in real time',
              'Rerouting decision takes 4–6 hours total',
              'Competitor ships around the disruption first',
            ].map((p, i) => (
              <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                <span style={{ color: '#dc2626', flexShrink: 0 }}>✗</span>
                <span style={{ fontSize: '13px', color: '#64748b', lineHeight: '1.5' }}>{p}</span>
              </div>
            ))}
          </div>

          <div style={{
            background: '#071a0f', border: '1px solid #16a34a33',
            borderRadius: '12px', padding: '24px'
          }}>
            <div style={{ fontSize: '18px', marginBottom: '12px' }}>✅</div>
            <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f1f5f9', marginBottom: '10px' }}>
              With NexusFlow
            </h3>
            {[
              'System detects cyclone signal in 0 seconds',
              'AI calculates 2 rerouting options in 8 seconds',
              'Rs. 2.3Cr exposure visible instantly on dashboard',
              'Manager accepts route in 1 click — 90 sec total',
              'Freight partner notified via Slack automatically',
            ].map((p, i) => (
              <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                <span style={{ color: '#16a34a', flexShrink: 0 }}>✓</span>
                <span style={{ fontSize: '13px', color: '#94a3b8', lineHeight: '1.5' }}>{p}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Tech stack */}
        <div style={{
          background: '#0d1829', border: '1px solid #1e3a5f',
          borderRadius: '12px', padding: '24px', marginBottom: '32px'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f1f5f9', marginBottom: '16px' }}>
            Tech Stack
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
            {[
              { name: 'React 18',            role: 'Frontend framework',      color: '#3b82f6' },
              { name: 'react-leaflet',       role: 'Live map',                color: '#16a34a' },
              { name: 'react-force-graph',   role: 'Network visualization',   color: '#8b5cf6' },
              { name: 'Supabase Realtime',   role: 'Live data subscriptions', color: '#06b6d4' },
              { name: 'FastAPI (Python)',     role: 'Backend + AI engine',     color: '#d97706' },
              { name: 'Tailwind CSS',        role: 'Styling',                 color: '#ec4899' },
            ].map(t => (
              <div key={t.name} style={{
                background: '#080f1e', borderRadius: '8px',
                padding: '12px', border: `1px solid ${t.color}22`
              }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#f1f5f9', marginBottom: '3px' }}>{t.name}</div>
                <div style={{ fontSize: '11px', color: '#475569' }}>{t.role}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Demo company */}
        <div style={{
          background: '#0d1829', border: '1px solid #1e3a5f',
          borderRadius: '12px', padding: '24px'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f1f5f9', marginBottom: '12px' }}>
            Demo Company — AuroraTex Industries
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
            {[
              { label: 'Industry',         value: 'Textile Export' },
              { label: 'Location',         value: 'Surat, Gujarat' },
              { label: 'Monthly Volume',   value: '80 containers' },
              { label: 'Primary Port',     value: 'JNPT, Mumbai' },
              { label: 'Supply chain nodes', value: '6 nodes' },
              { label: 'Markets served',   value: 'EU, US, Middle East' },
            ].map(d => (
              <div key={d.label} style={{ padding: '10px', background: '#080f1e', borderRadius: '6px' }}>
                <div style={{ fontSize: '10px', color: '#334155', marginBottom: '3px', fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{d.label}</div>
                <div style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '500' }}>{d.value}</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
