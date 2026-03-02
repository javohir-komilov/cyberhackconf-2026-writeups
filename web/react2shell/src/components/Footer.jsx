export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer style={{
      background: 'var(--bg-1)',
      borderTop: '1px solid var(--border)',
      marginTop: 'auto',
    }}>
      {/* Main footer grid */}
      <div className="container" style={{ padding: '48px 24px 32px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '40px',
          marginBottom: '40px',
        }}>
          {/* Brand */}
          <div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px',
            }}>
              <span style={{
                background: 'linear-gradient(135deg, var(--green), var(--cyan))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '22px',
                fontWeight: '900',
                letterSpacing: '2px',
              }}>
                ⬡ TECHMART
              </span>
            </div>
            <p style={{ color: 'var(--text-3)', fontSize: '13px', lineHeight: '1.7' }}>
              Elite hardware for elite builders. From enthusiast GPUs to server-grade storage — we deliver cutting-edge tech.
            </p>
            <div style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
              {['X', 'GH', 'DC', 'YT'].map((s) => (
                <div key={s} style={{
                  width: '32px', height: '32px',
                  background: 'var(--bg-2)',
                  border: '1px solid var(--border-b)',
                  borderRadius: '6px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '11px', color: 'var(--text-3)', cursor: 'pointer',
                  transition: 'var(--transition)',
                }}>{s}</div>
              ))}
            </div>
          </div>

          {/* Products */}
          <div>
            <h4 style={{
              fontSize: '11px', letterSpacing: '2px', textTransform: 'uppercase',
              color: 'var(--text-3)', marginBottom: '16px',
            }}>Products</h4>
            {['Graphics Cards', 'Processors', 'Memory & Storage', 'Monitors', 'Motherboards', 'Power Supplies'].map((item) => (
              <div key={item} style={{ marginBottom: '10px' }}>
                <span style={{
                  color: 'var(--text-2)', fontSize: '13px', cursor: 'pointer',
                  transition: 'var(--transition)',
                }}>{item}</span>
              </div>
            ))}
          </div>

          {/* Support */}
          <div>
            <h4 style={{
              fontSize: '11px', letterSpacing: '2px', textTransform: 'uppercase',
              color: 'var(--text-3)', marginBottom: '16px',
            }}>Support</h4>
            {['Order Tracking', 'Returns & Refunds', 'Warranty Info', 'Tech Support', 'Contact Us', 'FAQ'].map((item) => (
              <div key={item} style={{ marginBottom: '10px' }}>
                <span style={{
                  color: 'var(--text-2)', fontSize: '13px', cursor: 'pointer',
                }}>{item}</span>
              </div>
            ))}
          </div>

          {/* Trust badges */}
          <div>
            <h4 style={{
              fontSize: '11px', letterSpacing: '2px', textTransform: 'uppercase',
              color: 'var(--text-3)', marginBottom: '16px',
            }}>Security & Trust</h4>
            {[
              { icon: '🔒', label: 'SSL Encrypted' },
              { icon: '🛡️', label: 'WAF Protected' },
              { icon: '💳', label: 'Secure Payments' },
              { icon: '✅', label: 'Verified Seller' },
            ].map(({ icon, label }) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                marginBottom: '12px', color: 'var(--text-2)', fontSize: '13px',
              }}>
                <span>{icon}</span>
                <span>{label}</span>
              </div>
            ))}
            <div style={{
              marginTop: '12px',
              padding: '10px 12px',
              background: 'rgba(0,255,136,0.05)',
              border: '1px solid rgba(0,255,136,0.15)',
              borderRadius: '6px',
            }}>
              <p style={{ fontSize: '11px', color: 'var(--green)', marginBottom: '2px' }}>
                ◉ SecureShield WAF Active
              </p>
              <p style={{ fontSize: '10px', color: 'var(--text-3)' }}>
                v2.1.4 | All requests monitored
              </p>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '24px' }}>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '16px',
          }}>
            <p style={{ color: 'var(--text-3)', fontSize: '12px' }}>
              © {year} TechMart Inc. All rights reserved. · Privacy Policy · Terms of Service
            </p>

            {/* Powered by Javasec */}
            <a
              href="https://t.me/JavaSecuz"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                background: 'linear-gradient(135deg, rgba(0,212,255,0.08), rgba(139,92,246,0.08))',
                border: '1px solid rgba(0,212,255,0.2)',
                borderRadius: '20px',
                fontSize: '12px',
                color: 'var(--cyan)',
                textDecoration: 'none',
                transition: 'var(--transition)',
                fontWeight: '500',
                letterSpacing: '0.5px',
              }}
            >
              <span style={{ fontSize: '14px' }}>⚡</span>
              <span>Powered by</span>
              <span style={{
                background: 'linear-gradient(135deg, var(--cyan), var(--purple))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontWeight: '700',
                letterSpacing: '1px',
              }}>
                Javasec
              </span>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
