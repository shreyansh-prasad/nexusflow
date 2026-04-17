export default function HowItWorksPage() {
  const steps = [
    {
      icon: '📡',
      title: 'Signal Detection',
      color: '#3b82f6',
      desc: 'NexusFlow continuously monitors 4 live data feeds — IMD weather bulletins, port authority congestion APIs, global news sentiment NLP, and shipping registry updates.',
      details: ['Weather API — 94% confidence', 'Port Authority Feed — 88% confidence', 'News Sentiment NLP — 76% confidence', 'Shipping Registry — 61% confidence'],
    },
    {
      icon: '🧠',
      title: 'AI Risk Scoring',
      color: '#8b5cf6',
      desc: 'Each supply chain node gets a real-time risk score (0–100). When any score crosses a threshold, a cascade analysis fires to calculate how the disruption spreads across all 6 nodes.',
      details: ['Score < 40 → Green (Stable)', 'Score 40–70 → Amber (Warning)', 'Score > 70 → Red (Critical)', 'Cascade propagates in 500ms steps'],
    },
    {
      icon: '🗺️',
      title: 'Rerouting Calculation',
      color: '#16a34a',
      desc: 'Within seconds of a disruption, the engine calculates alternative routes. Each option is ranked by time delta, cost delta, risk reduction percentage, and freight partner availability.',
      details: ['Via Mundra: +36 hrs, Rs. 1.8L extra, 82% risk reduction', 'Via Chennai: +72 hrs, Rs. 3.2L extra, 95% risk reduction', 'Confidence scores based on partner data', 'One-click acceptance dispatches Slack notification'],
    },
    {
      icon: '⚡',
      title: 'One-Click Action',
      color: '#d97706',
      desc: 'The supply chain manager accepts a route with one click. NexusFlow instantly updates the live map, notifies the VP of Supply Chain via Slack, and initiates freight partner booking.',
      details: ['Map updates in real time', 'Slack message auto-drafted', 'Exposure drops from Rs. 2.3Cr to Rs. 12L', 'Total time: under 90 seconds'],
    },
  ];

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: '#080f1e', padding: '40px 60px' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>

        {/* Page header */}
        <div style={{ marginBottom: '40px' }}>
          <div style={{
            fontSize: '11px', color: '#3b82f6', fontWeight: '700',
            letterSpacing: '2px', marginBottom: '12px',
            fontFamily: 'JetBrains Mono, monospace'
          }}>
            HOW IT WORKS
          </div>
          <h1 style={{ fontSize: '36px', fontWeight: '800', color: '#f1f5f9', marginBottom: '14px', letterSpacing: '-0.5px' }}>
            From Signal to Action in Under 90 Seconds
          </h1>
          <p style={{ fontSize: '16px', color: '#64748b', lineHeight: '1.7', maxWidth: '620px' }}>
            NexusFlow monitors your entire supply chain 24/7 and converts raw signals into actionable rerouting decisions — automatically, before your competitors even know there's a problem.
          </p>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {steps.map((step, i) => (
            <div key={i} style={{
              background: '#0d1829',
              border: `1px solid ${step.color}33`,
              borderLeft: `4px solid ${step.color}`,
              borderRadius: '12px', padding: '28px 32px',
              display: 'flex', gap: '28px', alignItems: 'flex-start'
            }}>
              {/* Step number + icon */}
              <div style={{ flexShrink: 0, textAlign: 'center' }}>
                <div style={{
                  width: '52px', height: '52px', borderRadius: '12px',
                  background: step.color + '18', border: `1px solid ${step.color}44`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '26px', marginBottom: '8px'
                }}>
                  {step.icon}
                </div>
                <div style={{
                  fontSize: '11px', color: step.color, fontWeight: '700',
                  fontFamily: 'JetBrains Mono, monospace'
                }}>
                  STEP {i + 1}
                </div>
              </div>

              {/* Content */}
              <div style={{ flex: 1 }}>
                <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#f1f5f9', marginBottom: '10px' }}>
                  {step.title}
                </h2>
                <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: '1.7', marginBottom: '16px' }}>
                  {step.desc}
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {step.details.map((d, j) => (
                    <div key={j} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: step.color, flexShrink: 0 }} />
                      <span style={{ fontSize: '13px', color: '#64748b' }}>{d}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Timeline bar */}
        <div style={{
          marginTop: '40px', background: '#0d1829',
          border: '1px solid #1e3a5f', borderRadius: '12px', padding: '28px 32px'
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#f1f5f9', marginBottom: '20px' }}>
            Complete Timeline — Cyclone Warning Scenario
          </h2>
          <div style={{ display: 'flex', gap: '0', alignItems: 'center' }}>
            {[
              { time: '0s',   label: 'Signal detected',     color: '#3b82f6' },
              { time: '2s',   label: 'AI analysis',          color: '#8b5cf6' },
              { time: '5s',   label: 'Cascade calculated',   color: '#d97706' },
              { time: '8s',   label: 'Routes ready',         color: '#16a34a' },
              { time: '90s',  label: 'Route accepted',       color: '#4ade80' },
            ].map((t, i, arr) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', flex: i < arr.length-1 ? 1 : 0 }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '50%',
                    background: t.color + '22', border: `2px solid ${t.color}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '11px', fontWeight: '700', color: t.color,
                    fontFamily: 'JetBrains Mono, monospace', margin: '0 auto 8px'
                  }}>
                    {t.time}
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b', whiteSpace: 'nowrap' }}>{t.label}</div>
                </div>
                {i < arr.length - 1 && (
                  <div style={{ flex: 1, height: '1px', background: '#1e3a5f', margin: '0 4px 20px' }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
