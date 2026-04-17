import { useState } from 'react';
import DashboardPage  from './DashboardPage';
import HowItWorksPage from './HowItWorksPage';
import RoutesPage     from './RoutesPage';
import AboutPage      from './AboutPage';

export default function App() {
  const [page, setPage] = useState('dashboard');

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#080f1e', overflow: 'hidden' }}>

      {/* ── TOP NAV ── */}
      <nav style={{
        height: '54px', flexShrink: 0,
        background: '#060e1a',
        borderBottom: '1px solid #1e3a5f',
        display: 'flex', alignItems: 'center',
        padding: '0 24px', zIndex: 200
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginRight: '28px' }}>
          <svg width="32" height="32" viewBox="0 0 36 36" fill="none">
            <polygon points="18,2 31,9.5 31,26.5 18,34 5,26.5 5,9.5" fill="none" stroke="#1e3a5f" strokeWidth="1.5"/>
            <polygon points="18,6 28,11.5 28,24.5 18,30 8,24.5 8,11.5" fill="#0d1f3c" stroke="#1d4ed8" strokeWidth="1"/>
            <circle cx="18" cy="13" r="2.5" fill="#3b82f6"/>
            <circle cx="11" cy="21" r="2" fill="#60a5fa" opacity="0.9"/>
            <circle cx="25" cy="21" r="2" fill="#60a5fa" opacity="0.9"/>
            <circle cx="18" cy="26" r="1.8" fill="#93c5fd" opacity="0.7"/>
            <line x1="18" y1="13" x2="11" y2="21" stroke="#3b82f6" strokeWidth="1" opacity="0.7"/>
            <line x1="18" y1="13" x2="25" y2="21" stroke="#3b82f6" strokeWidth="1" opacity="0.7"/>
            <line x1="11" y1="21" x2="18" y2="26" stroke="#60a5fa" strokeWidth="0.8" opacity="0.5"/>
            <line x1="25" y1="21" x2="18" y2="26" stroke="#60a5fa" strokeWidth="0.8" opacity="0.5"/>
            <circle cx="18" cy="13" r="5" fill="#3b82f6" opacity="0.1">
              <animate attributeName="r" values="5;9;5" dur="2.8s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.1;0;0.1" dur="2.8s" repeatCount="indefinite"/>
            </circle>
          </svg>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '1px' }}>
            <span style={{
              fontSize: '18px', fontWeight: '800', letterSpacing: '-0.5px',
              background: 'linear-gradient(90deg,#93c5fd,#3b82f6)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
            }}>Nexus</span>
            <span style={{ fontSize: '18px', fontWeight: '300', color: '#e2e8f0' }}>Flow</span>
            <span style={{ fontSize: '11px', color: '#3b82f6', fontWeight: '700', marginLeft: '1px' }}>™</span>
          </div>
        </div>

        {/* Nav tabs */}
        {[
          { id: 'dashboard',  label: '📡  Live Dashboard' },
          { id: 'routes',     label: '🗺️  Route Planner'  },
          { id: 'howitworks', label: '⚙️  How It Works'   },
          { id: 'about',      label: 'ℹ️  About'           },
        ].map(item => (
          <button
            key={item.id}
            onClick={() => setPage(item.id)}
            style={{
              padding: '6px 18px', marginRight: '4px',
              borderRadius: '6px 6px 0 0',
              border: 'none',
              borderBottom: page === item.id ? '2px solid #3b82f6' : '2px solid transparent',
              background: page === item.id ? '#1d4ed815' : 'transparent',
              color: page === item.id ? '#60a5fa' : '#64748b',
              fontSize: '13px', fontWeight: page === item.id ? '600' : '400',
              cursor: 'pointer', transition: 'all 0.18s',
              height: '54px'
            }}
          >
            {item.label}
          </button>
        ))}

        {/* Live badge */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ position: 'relative', width: '8px', height: '8px' }}>
            <div className="animate-ping-slow" style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              background: '#4ade80', opacity: 0.5
            }}/>
            <div style={{ position: 'absolute', inset: '2px', borderRadius: '50%', background: '#16a34a' }}/>
          </div>
          <span style={{ fontSize: '12px', color: '#4ade80', fontWeight: '700', letterSpacing: '1px' }}>LIVE</span>
          <span style={{ fontSize: '11px', color: '#334155', fontFamily: 'JetBrains Mono, monospace' }}>
            AuroraTex Industries
          </span>
        </div>
      </nav>

      {/* ── PAGE CONTENT ── */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {page === 'dashboard'  && <DashboardPage  onNavigate={setPage} />}
        {page === 'routes'     && <RoutesPage     onNavigate={setPage} />}
        {page === 'howitworks' && <HowItWorksPage onNavigate={setPage} />}
        {page === 'about'      && <AboutPage      onNavigate={setPage} />}
      </div>
    </div>
  );
}