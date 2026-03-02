'use client';

import { useActionState, useState, useEffect } from 'react';
import { processCheckout } from '@/app/actions';

const initialState = null;

export default function CheckoutForm() {
  const [state, formAction, pending] = useActionState(processCheckout, initialState);
  const [cart, setCart] = useState([]);
  const [step, setStep] = useState('cart'); // cart | payment | done

  useEffect(() => {
    const load = () => {
      try {
        setCart(JSON.parse(localStorage.getItem('tm_cart') || '[]'));
      } catch {}
    };
    load();
    window.addEventListener('cartUpdated', load);
    return () => window.removeEventListener('cartUpdated', load);
  }, []);

  useEffect(() => {
    if (state?.success) setStep('done');
  }, [state]);

  const removeItem = (id) => {
    const updated = cart.filter((i) => i.id !== id);
    setCart(updated);
    localStorage.setItem('tm_cart', JSON.stringify(updated));
    window.dispatchEvent(new Event('cartUpdated'));
  };

  const updateQty = (id, delta) => {
    const updated = cart.map((i) =>
      i.id === id ? { ...i, qty: Math.max(1, (i.qty || 1) + delta) } : i
    );
    setCart(updated);
    localStorage.setItem('tm_cart', JSON.stringify(updated));
    window.dispatchEvent(new Event('cartUpdated'));
  };

  const subtotal = cart.reduce((s, i) => s + i.price * (i.qty || 1), 0);
  const tax = parseFloat((subtotal * 0.08).toFixed(2));
  const shipping = subtotal > 500 ? 0 : 14.99;
  const total = parseFloat((subtotal + tax + shipping).toFixed(2));

  /* ── Order success ── */
  if (step === 'done' && state?.success) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '60px 40px',
        background: 'var(--bg-card)',
        border: '1px solid rgba(0,255,136,0.25)',
        borderRadius: '16px',
        animation: 'slideIn 0.4s ease',
      }}>
        <div style={{ fontSize: '64px', marginBottom: '20px' }}>✅</div>
        <h2 style={{
          fontSize: '24px',
          fontWeight: '800',
          marginBottom: '8px',
          background: 'linear-gradient(135deg, var(--green), var(--cyan))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          Order Confirmed!
        </h2>
        <p style={{ color: 'var(--text-2)', marginBottom: '24px' }}>
          Your order has been placed successfully.
        </p>

        <div style={{
          background: 'var(--bg-2)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          padding: '20px',
          display: 'inline-block',
          textAlign: 'left',
          minWidth: '300px',
          marginBottom: '28px',
        }}>
          {[
            ['Order ID', state.orderId],
            ['Items', state.items],
            ['Subtotal', `$${state.subtotal?.toFixed(2)}`],
            ['Tax', `$${state.tax?.toFixed(2)}`],
            ['Shipping', state.shipping === 0 ? 'FREE' : `$${state.shipping}`],
            ['Total', `$${state.total?.toFixed(2)}`],
            ['Delivery', state.estimatedDelivery],
          ].map(([k, v]) => (
            <div key={k} style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '8px 0',
              borderBottom: '1px solid var(--border)',
              fontSize: '13px',
            }}>
              <span style={{ color: 'var(--text-3)' }}>{k}</span>
              <span style={{ color: k === 'Total' ? 'var(--green)' : 'var(--text-1)', fontWeight: k === 'Total' ? '700' : '400' }}>{v}</span>
            </div>
          ))}
        </div>

        <div>
          <button
            onClick={() => {
              localStorage.removeItem('tm_cart');
              window.dispatchEvent(new Event('cartUpdated'));
              window.location.href = '/';
            }}
            className="btn btn-primary"
            style={{ margin: '0 auto' }}
          >
            Continue Shopping →
          </button>
        </div>
      </div>
    );
  }

  /* ── Empty cart ── */
  if (cart.length === 0 && step !== 'done') {
    return (
      <div style={{
        textAlign: 'center',
        padding: '80px 40px',
        color: 'var(--text-3)',
      }}>
        <div style={{ fontSize: '64px', marginBottom: '20px', opacity: 0.4 }}>🛒</div>
        <h3 style={{ fontSize: '18px', color: 'var(--text-2)', marginBottom: '8px' }}>
          Your cart is empty
        </h3>
        <p style={{ fontSize: '14px', marginBottom: '24px' }}>
          Add some products to get started.
        </p>
        <a href="/" className="btn btn-outline" style={{ display: 'inline-flex' }}>
          Browse Products
        </a>
      </div>
    );
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 380px',
      gap: '28px',
      alignItems: 'start',
    }}>
      {/* Cart items */}
      <div>
        <h2 style={{
          fontSize: '18px',
          fontWeight: '700',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          🛒 Cart
          <span style={{
            background: 'var(--bg-2)',
            border: '1px solid var(--border-b)',
            borderRadius: '20px',
            padding: '2px 10px',
            fontSize: '12px',
            color: 'var(--text-2)',
          }}>
            {cart.length} item{cart.length !== 1 ? 's' : ''}
          </span>
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {cart.map((item) => (
            <div key={item.id} style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
            }}>
              <div style={{
                width: '56px',
                height: '56px',
                background: 'var(--bg-2)',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px',
                flexShrink: 0,
              }}>🎮</div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {item.name}
                </h4>
                <p style={{ fontSize: '11px', color: 'var(--text-3)', fontFamily: 'monospace' }}>
                  SKU: {item.sku || `TM-${item.id}`}
                </p>
              </div>

              {/* Qty controls */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                <button
                  onClick={() => updateQty(item.id, -1)}
                  style={{
                    width: '28px', height: '28px',
                    background: 'var(--bg-2)',
                    border: '1px solid var(--border-b)',
                    borderRadius: '6px',
                    color: 'var(--text-2)',
                    cursor: 'pointer',
                    fontSize: '16px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                >−</button>
                <span style={{ width: '24px', textAlign: 'center', fontSize: '14px', fontWeight: '600' }}>
                  {item.qty || 1}
                </span>
                <button
                  onClick={() => updateQty(item.id, 1)}
                  style={{
                    width: '28px', height: '28px',
                    background: 'var(--bg-2)',
                    border: '1px solid var(--border-b)',
                    borderRadius: '6px',
                    color: 'var(--text-2)',
                    cursor: 'pointer',
                    fontSize: '16px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                >+</button>
              </div>

              <div style={{
                textAlign: 'right',
                flexShrink: 0,
                minWidth: '80px',
              }}>
                <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--green)' }}>
                  ${(item.price * (item.qty || 1)).toLocaleString()}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-3)' }}>
                  ${item.price} each
                </div>
              </div>

              <button
                onClick={() => removeItem(item.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-3)',
                  cursor: 'pointer',
                  fontSize: '18px',
                  padding: '4px',
                  borderRadius: '4px',
                  transition: 'var(--transition)',
                  flexShrink: 0,
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'var(--pink)'}
                onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-3)'}
              >✕</button>
            </div>
          ))}
        </div>
      </div>

      {/* Order summary + checkout */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '16px',
        padding: '24px',
        position: 'sticky',
        top: '80px',
      }}>
        <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '20px' }}>
          Order Summary
        </h3>

        {[
          ['Subtotal', `$${subtotal.toFixed(2)}`],
          ['Tax (8%)', `$${tax.toFixed(2)}`],
          ['Shipping', subtotal > 500 ? 'FREE 🎉' : `$${shipping}`],
        ].map(([k, v]) => (
          <div key={k} style={{
            display: 'flex',
            justifyContent: 'space-between',
            padding: '10px 0',
            borderBottom: '1px solid var(--border)',
            fontSize: '14px',
          }}>
            <span style={{ color: 'var(--text-2)' }}>{k}</span>
            <span style={{ color: 'var(--text-1)' }}>{v}</span>
          </div>
        ))}

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          padding: '14px 0 20px',
          fontSize: '18px',
          fontWeight: '800',
        }}>
          <span>Total</span>
          <span style={{
            background: 'linear-gradient(135deg, var(--green), var(--cyan))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>${total.toFixed(2)}</span>
        </div>

        {/* Hidden form for Server Action */}
        <form action={formAction}>
          <input type="hidden" name="cartItems" value={JSON.stringify(cart)} />

          {state?.error && (
            <div style={{
              background: 'rgba(255,45,120,0.08)',
              border: '1px solid rgba(255,45,120,0.25)',
              borderRadius: '8px',
              padding: '10px 14px',
              marginBottom: '14px',
              fontSize: '13px',
              color: 'var(--pink)',
            }}>
              ⚠ {state.error}
            </div>
          )}

          <button
            type="submit"
            disabled={pending || cart.length === 0}
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '15px' }}
          >
            {pending ? (
              <>⟳ Processing...</>
            ) : (
              <>🔒 Place Order — ${total.toFixed(2)}</>
            )}
          </button>
        </form>

        {/* Security badges */}
        <div style={{
          marginTop: '16px',
          display: 'flex',
          justifyContent: 'center',
          gap: '16px',
          flexWrap: 'wrap',
        }}>
          {['🔒 SSL', '🛡 WAF', '💳 PCI'].map((b) => (
            <span key={b} style={{ fontSize: '11px', color: 'var(--text-3)' }}>{b}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
