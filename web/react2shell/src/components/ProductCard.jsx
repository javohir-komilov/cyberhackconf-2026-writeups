'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function ProductCard({ product }) {
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const discount = product.originalPrice
    ? Math.round((1 - product.price / product.originalPrice) * 100)
    : 0;

  const addToCart = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setAdding(true);

    try {
      const cart = JSON.parse(localStorage.getItem('tm_cart') || '[]');
      const idx = cart.findIndex((i) => i.id === product.id);
      if (idx >= 0) {
        cart[idx].qty = (cart[idx].qty || 1) + 1;
      } else {
        cart.push({
          id: product.id,
          name: product.name,
          price: product.price,
          qty: 1,
          sku: product.sku,
        });
      }
      localStorage.setItem('tm_cart', JSON.stringify(cart));
      window.dispatchEvent(new Event('cartUpdated'));
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } finally {
      setAdding(false);
    }
  };

  return (
    <Link href={`/product/${product.id}`} style={{ textDecoration: 'none', display: 'block' }}>
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        overflow: 'hidden',
        transition: 'all 0.25s ease',
        cursor: 'pointer',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = 'rgba(0,255,136,0.35)';
          e.currentTarget.style.boxShadow = '0 4px 24px rgba(0,255,136,0.08)';
          e.currentTarget.style.transform = 'translateY(-3px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'var(--border)';
          e.currentTarget.style.boxShadow = 'none';
          e.currentTarget.style.transform = 'translateY(0)';
        }}
      >
        {/* Image area */}
        <div style={{
          background: 'linear-gradient(135deg, var(--bg-2), var(--bg-3))',
          padding: '32px',
          textAlign: 'center',
          position: 'relative',
          borderBottom: '1px solid var(--border)',
          fontSize: '64px',
          lineHeight: 1,
        }}>
          {product.image}

          {/* Badges */}
          <div style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
          }}>
            {product.badge && (
              <span className={`badge ${product.badgeType}`}>
                {product.badge}
              </span>
            )}
            {discount > 0 && (
              <span className="badge badge-orange">-{discount}%</span>
            )}
          </div>

          {/* Stock indicator */}
          {product.stock <= 5 && (
            <div style={{
              position: 'absolute',
              bottom: '10px',
              right: '12px',
              fontSize: '11px',
              color: 'var(--orange)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}>
              <span className="dot dot-orange" />
              Only {product.stock} left
            </div>
          )}
        </div>

        {/* Content */}
        <div style={{ padding: '18px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Category */}
          <p style={{
            fontSize: '11px',
            color: 'var(--purple)',
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            marginBottom: '6px',
          }}>
            {product.category}
          </p>

          {/* Name */}
          <h3 style={{
            fontSize: '15px',
            fontWeight: '700',
            color: 'var(--text-1)',
            marginBottom: '8px',
            lineHeight: '1.3',
          }}>
            {product.name}
          </h3>

          {/* Rating */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            marginBottom: '10px',
          }}>
            <div style={{ display: 'flex', gap: '2px' }}>
              {[1,2,3,4,5].map((s) => (
                <span key={s} style={{
                  fontSize: '11px',
                  color: s <= Math.round(product.rating) ? 'var(--orange)' : 'var(--text-4)',
                }}>★</span>
              ))}
            </div>
            <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>
              {product.rating} ({product.reviews})
            </span>
          </div>

          {/* Specs preview */}
          <div style={{ flex: 1, marginBottom: '16px' }}>
            {product.specs.slice(0, 3).map((spec) => (
              <div key={spec} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginBottom: '4px',
              }}>
                <span style={{ color: 'var(--green)', fontSize: '10px' }}>▸</span>
                <span style={{ fontSize: '12px', color: 'var(--text-2)' }}>{spec}</span>
              </div>
            ))}
          </div>

          {/* Price & CTA */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '12px',
            borderTop: '1px solid var(--border)',
          }}>
            <div>
              <div className="price">${product.price.toLocaleString()}</div>
              {product.originalPrice && (
                <div style={{
                  fontSize: '12px',
                  color: 'var(--text-3)',
                  textDecoration: 'line-through',
                }}>
                  ${product.originalPrice.toLocaleString()}
                </div>
              )}
            </div>

            <button
              onClick={addToCart}
              disabled={adding}
              style={{
                background: added
                  ? 'linear-gradient(135deg, var(--green), var(--cyan))'
                  : 'rgba(0,255,136,0.1)',
                border: `1px solid ${added ? 'transparent' : 'rgba(0,255,136,0.3)'}`,
                borderRadius: '8px',
                padding: '8px 14px',
                color: added ? '#000' : 'var(--green)',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                letterSpacing: '0.5px',
              }}
            >
              {adding ? '...' : added ? '✓ Added' : '+ Cart'}
            </button>
          </div>
        </div>
      </div>
    </Link>
  );
}
