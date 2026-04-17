const iconMap = { weather: '🌀', port: '⚓', news: '📰', system: '🤖' };
const severityColors = ['', '#16a34a', '#65a30d', '#d97706', '#ea580c', '#dc2626'];
const severityLabel  = ['', 'LOW', 'LOW', 'MED', 'HIGH', 'CRIT'];

export default function AlertCard({ alert, index }) {
  return (
    <div
      className="animate-slide-left"
      style={{
        animationDelay: `${index * 90}ms`,
        background: '#0d1520',
        border: '1px solid #dc262633',
        borderLeft: '3px solid #dc2626',
        borderRadius: '8px', padding: '12px', marginBottom: '10px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '18px', flexShrink: 0 }}>{iconMap[alert.signalType] || '⚠'}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '13px', fontWeight: '600', color: '#f1f5f9' }}>{alert.title}</div>
          <div style={{ fontSize: '11px', color: '#475569', marginTop: '1px' }}>{alert.timeAgo}</div>
        </div>
      </div>

      {/* Severity bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '3px', marginBottom: '8px' }}>
        {[1,2,3,4,5].map(b => (
          <div key={b} style={{
            flex: 1, height: '4px', borderRadius: '2px',
            background: b <= alert.severity ? severityColors[alert.severity] : '#1e293b',
            transition: 'background 0.4s'
          }} />
        ))}
        <span style={{
          fontSize: '10px', color: severityColors[alert.severity],
          marginLeft: '5px', fontWeight: '700',
          fontFamily: 'JetBrains Mono, monospace', flexShrink: 0
        }}>
          {severityLabel[alert.severity]}
        </span>
      </div>

      <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', lineHeight: '1.5' }}>
        {alert.description}
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px',
        background: '#0a1018', borderRadius: '5px', padding: '8px'
      }}>
        <div>
          <div style={{ fontSize: '10px', color: '#475569', marginBottom: '2px' }}>Exposure</div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', color: '#f97316', fontWeight: '600', fontSize: '13px' }}>
            {alert.exposure}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#475569', marginBottom: '2px' }}>Time to impact</div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', color: '#fbbf24', fontWeight: '600', fontSize: '13px' }}>
            {alert.timeToImpact}
          </div>
        </div>
      </div>
    </div>
  );
}
