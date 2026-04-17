const typeIcon = { weather: '🌀', port: '⚓', news: '📰', system: '🤖' };

export default function DisruptionTimeline({ events }) {
  return (
    <div>
      <div style={{
        fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase',
        letterSpacing: '0.8px', marginBottom: '10px'
      }}>Disruption Timeline</div>

      <div style={{ position: 'relative' }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: '14px', top: '8px',
          bottom: 0, width: '1px', background: '#334155'
        }} />

        {events.map((e, i) => (
          <div key={i} className="animate-fade-up" style={{
            animationDelay: `${i * 60}ms`,
            display: 'flex', gap: '10px', marginBottom: '14px',
            position: 'relative'
          }}>
            {/* Dot */}
            <div style={{
              width: '28px', height: '28px', borderRadius: '50%',
              background: e.severity >= 4 ? '#dc262622' : '#1e293b',
              border: `1px solid ${e.severity >= 4 ? '#dc2626' : '#334155'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '12px', flexShrink: 0, zIndex: 1
            }}>
              {typeIcon[e.type] || '●'}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#f1f5f9' }}>
                {e.title}
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>{e.location}</div>
              <div style={{
                fontSize: '10px', color: '#64748b',
                fontFamily: 'JetBrains Mono, monospace', marginTop: '2px'
              }}>{e.time}</div>
            </div>
            {e.severity >= 4 && (
              <div style={{
                fontSize: '9px', padding: '2px 5px', borderRadius: '3px',
                background: '#dc262622', color: '#ef4444', border: '1px solid #dc262644',
                height: 'fit-content', alignSelf: 'center', fontWeight: '600'
              }}>HIGH</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}