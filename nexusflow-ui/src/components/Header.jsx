export default function Header({ disrupted }) {
  return (
    <div style={{
      background: '#080f1e',
      borderBottom: '1px solid #1e3a5f',
      padding: '0 24px',
      height: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexShrink: 0,
      zIndex: 10,
      position: 'relative',
      boxShadow: '0 1px 0 #0d2240'
    }}>

      {/* ── LOGO + BRAND ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>

        {/* SVG Node-Network Logo */}
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Outer hexagon ring */}
          <polygon
            points="18,2 31,9.5 31,26.5 18,34 5,26.5 5,9.5"
            fill="none"
            stroke="#1e3a5f"
            strokeWidth="1.5"
          />
          {/* Inner glow hexagon */}
          <polygon
            points="18,6 28,11.5 28,24.5 18,30 8,24.5 8,11.5"
            fill="#0d1f3c"
            stroke="#1d4ed8"
            strokeWidth="1"
            opacity="0.8"
          />
          {/* Network nodes */}
          <circle cx="18" cy="13" r="2.5" fill="#3b82f6" />
          <circle cx="11" cy="21" r="2"   fill="#60a5fa" opacity="0.9" />
          <circle cx="25" cy="21" r="2"   fill="#60a5fa" opacity="0.9" />
          <circle cx="18" cy="26" r="1.8" fill="#93c5fd" opacity="0.7" />
          {/* Connecting lines */}
          <line x1="18" y1="13" x2="11" y2="21" stroke="#3b82f6" strokeWidth="1"   opacity="0.7" />
          <line x1="18" y1="13" x2="25" y2="21" stroke="#3b82f6" strokeWidth="1"   opacity="0.7" />
          <line x1="11" y1="21" x2="18" y2="26" stroke="#60a5fa" strokeWidth="0.8" opacity="0.5" />
          <line x1="25" y1="21" x2="18" y2="26" stroke="#60a5fa" strokeWidth="0.8" opacity="0.5" />
          <line x1="11" y1="21" x2="25" y2="21" stroke="#60a5fa" strokeWidth="0.8" opacity="0.4" />
          {/* Center pulse dot */}
          <circle cx="18" cy="13" r="4.5" fill="#3b82f6" opacity="0.15">
            <animate attributeName="r" values="4.5;7;4.5" dur="2.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.15;0;0.15" dur="2.5s" repeatCount="indefinite" />
          </circle>
        </svg>

        {/* Wordmark */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '2px' }}>
            <span style={{
              fontSize: '19px',
              fontWeight: '800',
              letterSpacing: '-0.5px',
              background: 'linear-gradient(90deg, #60a5fa, #3b82f6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontFamily: "'Inter', sans-serif"
            }}>Nexus</span>
            <span style={{
              fontSize: '19px',
              fontWeight: '300',
              letterSpacing: '-0.3px',
              color: '#e2e8f0',
              fontFamily: "'Inter', sans-serif"
            }}>Flow</span>
            <span style={{
              fontSize: '11px',
              color: '#3b82f6',
              fontWeight: '700',
              marginLeft: '1px',
              alignSelf: 'flex-start',
              marginTop: '3px'
            }}>™</span>
          </div>
          <div style={{
            fontSize: '9px',
            letterSpacing: '2px',
            color: '#334155',
            fontWeight: '600',
            textTransform: 'uppercase',
            fontFamily: "'JetBrains Mono', monospace"
          }}>
            SUPPLY CHAIN INTELLIGENCE
          </div>
        </div>

        {/* Divider */}
        <div style={{ width: '1px', height: '28px', background: '#1e3a5f', margin: '0 4px' }} />

        {/* Company */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ color: '#cbd5e1', fontSize: '13px', fontWeight: '500' }}>
            AuroraTex Industries
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{
              fontSize: '9px', fontWeight: '700',
              background: '#0d2d4a', color: '#38bdf8',
              padding: '1px 6px', borderRadius: '3px',
              border: '1px solid #1e4976',
              letterSpacing: '0.5px'
            }}>TEXTILE EXPORTER</span>
            <span style={{ color: '#334155', fontSize: '9px' }}>SURAT, GJ</span>
          </div>
        </div>
      </div>

      {/* ── CENTER — disruption banner ── */}
      <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
        {disrupted ? (
          <div className="animate-fade-up" style={{
            background: '#1a0a0a',
            border: '1px solid #dc2626',
            borderRadius: '6px',
            padding: '5px 16px',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}>
            <div style={{
              width: '6px', height: '6px', borderRadius: '50%',
              background: '#ef4444',
              boxShadow: '0 0 6px #ef4444'
            }} />
            <span style={{ fontSize: '11px', fontWeight: '700', color: '#ef4444', letterSpacing: '1px' }}>
              ACTIVE DISRUPTION — JNPT PORT
            </span>
            <div style={{
              width: '6px', height: '6px', borderRadius: '50%',
              background: '#ef4444',
              boxShadow: '0 0 6px #ef4444'
            }} />
          </div>
        ) : (
          <div style={{
            background: '#0a1a0f',
            border: '1px solid #16a34a33',
            borderRadius: '6px',
            padding: '5px 16px',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}>
            <div style={{
              width: '6px', height: '6px', borderRadius: '50%',
              background: '#16a34a'
            }} />
            <span style={{ fontSize: '11px', color: '#4ade80', letterSpacing: '0.5px', fontWeight: '500' }}>
              ALL SYSTEMS NOMINAL · 6 NODES ACTIVE
            </span>
          </div>
        )}
      </div>

      {/* ── RIGHT — live badge + stats ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>

        {/* Container count */}
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '1px'
        }}>
          <span style={{
            fontSize: '16px', fontWeight: '700',
            fontFamily: "'JetBrains Mono', monospace",
            color: '#f1f5f9'
          }}>80</span>
          <span style={{ fontSize: '9px', color: '#475569', letterSpacing: '1px', textTransform: 'uppercase' }}>
            containers/mo
          </span>
        </div>

        <div style={{ width: '1px', height: '24px', background: '#1e3a5f' }} />

        {/* LIVE badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ position: 'relative', width: '10px', height: '10px' }}>
            <div className="animate-ping-slow" style={{
              position: 'absolute', inset: 0,
              borderRadius: '50%',
              background: disrupted ? '#ef4444' : '#4ade80',
              opacity: 0.5
            }} />
            <div style={{
              position: 'absolute', inset: '2px',
              borderRadius: '50%',
              background: disrupted ? '#dc2626' : '#16a34a'
            }} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
            <span style={{
              fontSize: '12px', fontWeight: '700',
              color: disrupted ? '#ef4444' : '#4ade80',
              letterSpacing: '1.5px'
            }}>LIVE</span>
            <span style={{
              fontSize: '8px', color: '#334155',
              letterSpacing: '0.5px', fontFamily: "'JetBrains Mono', monospace"
            }}>
              {disrupted ? 'DISRUPTED' : 'STABLE'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}