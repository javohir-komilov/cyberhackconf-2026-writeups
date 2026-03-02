'use client';

import { useState } from 'react';

export default function AddToCartButton({ product }) {
  const [state, setState] = useState('idle'); // idle | adding | added

  const handleClick = () => {
    setState('adding');
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
      setState('added');
      setTimeout(() => setState('idle'), 2000);
    } catch {
      setState('idle');
    }
  };

  const labels = { idle: '🛒 Add to Cart', adding: '⟳ Adding...', added: '✓ Added!' };
  const styles = {
    idle: {
      background: 'linear-gradient(135deg, var(--green), var(--cyan))',
      color: '#000',
    },
    adding: {
      background: 'rgba(0,255,136,0.2)',
      color: 'var(--green)',
    },
    added: {
      background: 'linear-gradient(135deg, var(--green), var(--cyan))',
      color: '#000',
    },
  };

  return (
    <button
      onClick={handleClick}
      disabled={state === 'adding'}
      className="btn"
      style={{
        flex: 1,
        justifyContent: 'center',
        padding: '14px',
        fontSize: '15px',
        border: 'none',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        ...styles[state],
      }}
    >
      {labels[state]}
    </button>
  );
}
