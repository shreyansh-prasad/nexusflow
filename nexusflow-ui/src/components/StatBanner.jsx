import { useEffect, useState } from 'react';
import { useRef } from 'react';


const formatRupees = (amount) => {
  if (amount >= 10000000) return `Rs. ${(amount / 10000000).toFixed(1)}Cr`;
  if (amount >= 100000)   return `Rs. ${(amount / 100000).toFixed(1)}L`;
  if (amount >= 1000)     return `Rs. ${(amount / 1000).toFixed(0)}K`;
  return `Rs. ${amount}`;
};

function StatCard({ label, value, sub, color, flash }) {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    const card = cardRef.current;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -8;
    const rotateY = ((x - centerX) / centerX) * 8;
    card.style.transform = `perspective(600px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.03)`;
  };

  const handleMouseLeave = () => {
    cardRef.current.style.transform = 'perspective(600px) rotateX(0deg) rotateY(0deg) scale(1)';
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        // ... all your existing styles ...
        transition: 'transform 0.15s ease, box-shadow 0.15s ease',
        cursor: 'default'
      }}
    >
      {/* existing content */}
    </div>
  );
}

export default function StatBanner({ disrupted }) {
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    if (disrupted) {
      setFlash(true);
      const t = setTimeout(() => setFlash(false), 2000);
      return () => clearTimeout(t);
    }
  }, [disrupted]);

  return (
    <div style={{
      display: 'flex', gap: '12px', padding: '12px 24px',
      background: '#0f172a', borderBottom: '1px solid #334155',
      flexShrink: 0
    }}>
      <StatCard
        label="Active Alerts"
        value={disrupted ? '3' : '0'}
        sub={disrupted ? "2 high severity" : "All clear"}
        color={disrupted ? '#dc2626' : '#16a34a'}
        flash={flash}
      />
      <StatCard
        label="Exposure at Risk"
        value={disrupted ? 'Rs. 2.3Cr' : 'Rs. 0'}
        sub={disrupted ? "3 active shipments" : "No exposure"}
        color={disrupted ? '#d97706' : '#16a34a'}
        flash={flash}
      />
      <StatCard
        label="Resilience Score"
        value={disrupted ? '61' : '84'}
        sub={disrupted ? "↓ from 84" : "Optimal"}
        color={disrupted ? '#d97706' : '#3b82f6'}
        flash={flash}
      />
      <StatCard
        label="Routes Rerouted Today"
        value={disrupted ? '2' : '0'}
        sub={disrupted ? "Via Mundra, Chennai" : "No rerouting needed"}
        color={disrupted ? '#3b82f6' : '#94a3b8'}
        flash={flash}
      />
    </div>
  );
}
function AnimatedNumber({ target }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = parseInt(target) || 0;
    if (start === end) { setDisplay(end); return; }
    const duration = 800;
    const step = (end - start) / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setDisplay(end); clearInterval(timer); }
      else setDisplay(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [target]);
  return <>{display}</>;
}