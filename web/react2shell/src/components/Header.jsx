'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Header() {
  const [cartCount, setCartCount] = useState(0);
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const updateCart = () => {
      try {
        const cart = JSON.parse(localStorage.getItem('tm_cart') || '[]');
        setCartCount(cart.reduce((s, i) => s + (i.qty || 1), 0));
      } catch {}
    };
    updateCart();
    window.addEventListener('storage', updateCart);
    window.addEventListener('cartUpdated', updateCart);
    return () => {
      window.removeEventListener('storage', updateCart);
      window.removeEventListener('cartUpdated', updateCart);
    };
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      background: scrolled
        ? 'rgba(3,3,5,0.95)'
        : 'var(--bg-1)',
      backdropFilter: scrolled ? 'blur(20px)' : 'none',
      borderBottom: '1px solid var(--border)',
      transition: 'all 0.3s ease',
    }}>
      {/* Top bar */}
      <div style={{
        background: 'linear-gradient(90deg, var(--green), var(--cyan), var(--purple))',
        height: '2px',
      }} />

      {/* Announcement bar */}
      <div style={{
        background: 'rgba(0,255,136,0.05)',
        borderBottom: '1px solid rgba(0,255,136,0.08)',
        padding: '6px 0',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: '12px', color: 'var(--green)', letterSpacing: '1px' }}>
          🚀 FREE SHIPPING on orders over $500 · All prices include VAT · 30-day returns
        </p>
      </div>

      {/* Main nav */}
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 24px',
        gap: '24px',
      }}>
        {/* Logo */}
        <Link href="/" style={{ textDecoration: 'none', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px', height: '36px',
              background: 'linear-gradient(135deg, var(--green), var(--cyan))',
              borderRadius: '8px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '18px',
              boxShadow: '0 0 12px rgba(0,255,136,0.3)',
            }}>⬡</div>
            <div>
              <div style={{
                fontSize: '18px',
                fontWeight: '900',
                letterSpacing: '3px',
                background: 'linear-gradient(135deg, var(--green), var(--cyan))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                lineHeight: 1,
              }}>TECHMART</div>
              <div style={{
                fontSize: '9px',
                letterSpacing: '3px',
                color: 'var(--text-3)',
                textTransform: 'uppercase',
              }}>Elite Hardware</div>
            </div>
          </div>
        </Link>

        {/* Nav links */}
        <nav style={{
          display: 'flex',
          gap: '4px',
          flex: 1,
          justifyContent: 'center',
          maxWidth: '500px',
        }}>
          {[
            { label: 'Home', href: '/' },
            { label: 'GPUs', href: '/?cat=GPU' },
            { label: 'CPUs', href: '/?cat=CPU' },
            { label: 'Storage', href: '/?cat=SSD' },
            { label: 'Monitors', href: '/?cat=Monitor' },
            { label: 'Deals', href: '/?sale=1' },
          ].map(({ label, href }) => (
            <Link
              key={label}
              href={href}
              style={{
                color: 'var(--text-2)',
                fontSize: '13px',
                fontWeight: '500',
                padding: '6px 12px',
                borderRadius: '6px',
                transition: 'var(--transition)',
                textDecoration: 'none',
                letterSpacing: '0.3px',
              }}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          {/* Search */}
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            style={{
              background: 'var(--bg-2)',
              border: '1px solid var(--border-b)',
              borderRadius: '8px',
              padding: '8px 12px',
              color: 'var(--text-3)',
              cursor: 'pointer',
              fontSize: '16px',
              transition: 'var(--transition)',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}
          >
            🔍
            <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>Search...</span>
          </button>

          {/* Account */}
          <button style={{
            background: 'var(--bg-2)',
            border: '1px solid var(--border-b)',
            borderRadius: '8px',
            padding: '8px 10px',
            color: 'var(--text-2)',
            cursor: 'pointer',
            fontSize: '16px',
          }}>👤</button>

          {/* Cart */}
          <Link href="/cart" style={{ textDecoration: 'none' }}>
            <button style={{
              position: 'relative',
              background: cartCount > 0
                ? 'linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,212,255,0.15))'
                : 'var(--bg-2)',
              border: `1px solid ${cartCount > 0 ? 'rgba(0,255,136,0.3)' : 'var(--border-b)'}`,
              borderRadius: '8px',
              padding: '8px 14px',
              color: cartCount > 0 ? 'var(--green)' : 'var(--text-2)',
              cursor: 'pointer',
              fontSize: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'var(--transition)',
            }}>
              🛒
              {cartCount > 0 && (
                <span style={{
                  background: 'var(--pink)',
                  color: '#fff',
                  borderRadius: '10px',
                  padding: '1px 7px',
                  fontSize: '11px',
                  fontWeight: '700',
                  minWidth: '20px',
                  textAlign: 'center',
                }}>
                  {cartCount}
                </span>
              )}
            </button>
          </Link>
        </div>
      </div>

      {/* Search overlay */}
      {searchOpen && (
        <div style={{
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-1)',
          padding: '16px 24px',
        }}>
          <div className="container" style={{ padding: 0 }}>
            <input
              autoFocus
              className="input"
              placeholder="Search products, SKUs, categories..."
              onBlur={() => setTimeout(() => setSearchOpen(false), 200)}
              style={{ maxWidth: '600px' }}
            />
          </div>
        </div>
      )}
    </header>
  );
}
