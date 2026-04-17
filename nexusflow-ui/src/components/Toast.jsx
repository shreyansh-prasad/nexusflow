import { useEffect } from 'react';

export default function Toast({ message, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 8000);
    return () => clearTimeout(t);
  }, [onClose]);

  if (!message) return null;

  return (
    <div style={{
      position: 'fixed', bottom: '24px', left: '50%',
      transform: 'translateX(-50%)',
      background: '#1e293b', border: '1px solid #16a34a',
      borderLeft: '4px solid #16a34a',
      borderRadius: '10px', padding: '14px 20px',
      maxWidth: '520px', width: '90%',
      zIndex: 9999, boxShadow: '0 8px 32px #00000088',
      animation: 'fadeInUp 0.4s ease'
    }}>
      <div style={{ fontSize: '12px', fontWeight: '600', color: '#4ade80', marginBottom: '4px' }}>
        ✅ Slack Notification Sent
      </div>
      <div style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.5' }}>{message}</div>
      <button onClick={onClose} style={{
        position: 'absolute', top: '8px', right: '12px',
        background: 'none', border: 'none', color: '#94a3b8',
        cursor: 'pointer', fontSize: '16px'
      }}>×</button>
    </div>
  );
}