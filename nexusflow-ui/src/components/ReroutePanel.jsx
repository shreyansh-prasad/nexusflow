const routes = [
  {
    id: 'mundra',
    name: 'Via Mundra Port',
    emoji: '🟡',
    timeDelta: '+36 hrs',
    costDelta: 'Rs. 1.8L extra',
    riskReduction: 82,
    confidence: 91,
    badge: 'Recommended',
    badgeColor: '#3b82f6',
  },
  {
    id: 'chennai',
    name: 'Via Chennai Port',
    emoji: '🟢',
    timeDelta: '+72 hrs',
    costDelta: 'Rs. 3.2L extra',
    riskReduction: 95,
    confidence: 87,
    badge: 'Safest',
    badgeColor: '#16a34a',
  },
];

export default function ReroutePanel({ visible, onAccept, acceptedRoute }) {
  if (!visible) return null;

  return (
    <div className="animate-fade-up" style={{ marginTop: '4px' }}>
      <div style={{
        fontSize: '11px', color: '#475569',
        textTransform: 'uppercase', letterSpacing: '1px',
        marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px',
        fontFamily: 'JetBrains Mono, monospace'
      }}>
        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3b82f6' }} />
        Rerouting Options
      </div>

      {routes.map(r => {
        const isAccepted = acceptedRoute === r.id;
        return (
          <div key={r.id} style={{
            background: isAccepted ? '#071a0f' : '#0d1520',
            border: `1px solid ${isAccepted ? '#16a34a' : '#334155'}`,
            borderRadius: '8px', padding: '12px', marginBottom: '8px',
            transition: 'all 0.3s ease'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: '#f1f5f9' }}>
                {r.emoji} {r.name}
              </span>
              <span style={{
                fontSize: '10px', padding: '2px 7px', borderRadius: '4px',
                background: r.badgeColor + '22', color: r.badgeColor,
                border: `1px solid ${r.badgeColor}44`, fontWeight: '700',
                fontFamily: 'JetBrains Mono, monospace'
              }}>{r.badge}</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px', marginBottom: '8px' }}>
              {[
                { label: 'Time delta',     value: r.timeDelta,              color: '#fbbf24' },
                { label: 'Cost delta',     value: r.costDelta,              color: '#f97316' },
                { label: 'Risk reduction', value: `↓ ${r.riskReduction}%`, color: '#4ade80' },
                { label: 'Confidence',     value: `${r.confidence}%`,      color: '#3b82f6' },
              ].map(stat => (
                <div key={stat.label} style={{ background: '#0a1018', borderRadius: '4px', padding: '6px 7px' }}>
                  <div style={{ fontSize: '10px', color: '#475569', marginBottom: '2px' }}>{stat.label}</div>
                  <div style={{
                    fontSize: '12px', fontFamily: 'JetBrains Mono, monospace',
                    color: stat.color, fontWeight: '600'
                  }}>{stat.value}</div>
                </div>
              ))}
            </div>

            <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', marginBottom: '8px' }}>
              <div style={{
                height: '100%', width: `${r.confidence}%`, background: r.badgeColor,
                borderRadius: '2px', transition: 'width 1s ease',
                boxShadow: `0 0 6px ${r.badgeColor}66`
              }} />
            </div>

            {!isAccepted ? (
              <button
                onClick={() => onAccept(r)}
                style={{
                  width: '100%', padding: '8px', borderRadius: '6px',
                  background: '#1d4ed8', border: '1px solid #3b82f6',
                  color: '#fff', fontSize: '12px', fontWeight: '700',
                  cursor: 'pointer', transition: 'all 0.2s',
                  letterSpacing: '0.5px', fontFamily: 'JetBrains Mono, monospace'
                }}
                onMouseOver={e => e.target.style.background = '#2563eb'}
                onMouseOut={e =>  e.target.style.background = '#1d4ed8'}
              >
                ✓ ACCEPT ROUTE
              </button>
            ) : (
              <div style={{
                textAlign: 'center', color: '#4ade80', fontSize: '12px',
                fontWeight: '700', padding: '8px',
                fontFamily: 'JetBrains Mono, monospace',
                background: '#071a0f', borderRadius: '6px',
                border: '1px solid #16a34a44'
              }}>
                ✅ ACTIVE — MAP UPDATED
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
