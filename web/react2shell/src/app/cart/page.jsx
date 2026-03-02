import CheckoutForm from '@/components/CheckoutForm';

export const metadata = {
  title: 'Cart & Checkout — TechMart',
};

export default function CartPage() {
  return (
    <>
      {/* Page header */}
      <div style={{
        background: 'linear-gradient(180deg, var(--bg-1) 0%, var(--bg-0) 100%)',
        borderBottom: '1px solid var(--border)',
        padding: '40px 0',
      }}>
        <div className="container">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            marginBottom: '8px',
          }}>
            <div style={{
              width: '40px', height: '40px',
              background: 'linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,212,255,0.1))',
              border: '1px solid rgba(0,255,136,0.25)',
              borderRadius: '10px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '20px',
            }}>🛒</div>
            <h1 style={{ fontSize: '28px', fontWeight: '800' }}>
              Checkout
            </h1>
          </div>
          <p style={{ color: 'var(--text-3)', fontSize: '14px', marginLeft: '54px' }}>
            Review your cart and place your order securely.
          </p>

          {/* Steps indicator */}
          <div style={{
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
            marginTop: '24px',
            marginLeft: '54px',
          }}>
            {[
              { n: 1, label: 'Cart', active: true },
              { n: 2, label: 'Payment', active: false },
              { n: 3, label: 'Confirmation', active: false },
            ].map(({ n, label, active }, i) => (
              <div key={n} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: '28px', height: '28px',
                  borderRadius: '50%',
                  background: active
                    ? 'linear-gradient(135deg, var(--green), var(--cyan))'
                    : 'var(--bg-2)',
                  border: active ? 'none' : '1px solid var(--border-b)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: '700',
                  color: active ? '#000' : 'var(--text-3)',
                }}>{n}</div>
                <span style={{
                  fontSize: '13px',
                  color: active ? 'var(--text-1)' : 'var(--text-3)',
                  fontWeight: active ? '600' : '400',
                }}>{label}</span>
                {i < 2 && (
                  <div style={{
                    width: '32px',
                    height: '1px',
                    background: 'var(--border-b)',
                    margin: '0 4px',
                  }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Checkout form */}
      <div className="section">
        <div className="container">
          <CheckoutForm />
        </div>
      </div>

      {/* Security notice */}
      <div style={{
        background: 'var(--bg-1)',
        borderTop: '1px solid var(--border)',
        padding: '20px 0',
      }}>
        <div className="container">
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '32px',
            flexWrap: 'wrap',
          }}>
            {[
              { icon: '🔒', text: '256-bit SSL encryption' },
              { icon: '🛡️', text: 'WAF protected endpoint' },
              { icon: '💳', text: 'PCI DSS compliant' },
              { icon: '🔍', text: 'All requests monitored' },
            ].map(({ icon, text }) => (
              <div key={text} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                color: 'var(--text-3)',
              }}>
                <span>{icon}</span>
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
