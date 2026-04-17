const signals = [
  { label: 'Weather API', status: 'live', value: 94 },
  { label: 'Port Authority Feed', status: 'live', value: 88 },
  { label: 'News Sentiment NLP', status: 'live', value: 76 },
  { label: 'Shipping Registry', status: 'delayed', value: 61 },
];

export default function SignalConfidence() {
  return (
    <div style={{ marginTop: '16px' }}>
      <div style={{
        fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase',
        letterSpacing: '0.8px', marginBottom: '10px'
      }}>Signal Confidence</div>

      {signals.map((s, i) => (
        <div key={i} style={{ marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', color: '#cbd5e1' }}>{s.label}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: s.status === 'live' ? '#16a34a' : '#d97706'
              }} />
              <span style={{
                fontSize: '11px', fontFamily: 'JetBrains Mono, monospace',
                color: s.value > 80 ? '#4ade80' : s.value > 65 ? '#fbbf24' : '#f87171'
              }}>{s.value}%</span>
            </div>
          </div>
          <div style={{ height: '3px', background: '#334155', borderRadius: '2px' }}>
            <div style={{
              height: '100%',
              width: `${s.value}%`,
              borderRadius: '2px',
              background: s.value > 80 ? '#16a34a' : s.value > 65 ? '#d97706' : '#dc2626',
              transition: 'width 1s ease'
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}