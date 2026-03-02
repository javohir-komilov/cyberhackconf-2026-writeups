import ProductCard from '@/components/ProductCard';
import { products } from '@/lib/products';

export default function HomePage({ searchParams }) {
  const cat = searchParams?.cat;
  const sale = searchParams?.sale;

  const filtered = products.filter((p) => {
    if (cat && p.category !== cat) return false;
    if (sale && !p.originalPrice) return false;
    return true;
  });

  const categories = [...new Set(products.map((p) => p.category))];

  return (
    <>
      {/* Hero */}
      <section style={{
        background: 'linear-gradient(180deg, var(--bg-1) 0%, var(--bg-0) 100%)',
        borderBottom: '1px solid var(--border)',
        padding: '72px 0',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Background grid */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(0,255,136,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,255,136,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          pointerEvents: 'none',
        }} />

        {/* Glow orbs */}
        <div style={{
          position: 'absolute', top: '-100px', left: '10%',
          width: '400px', height: '400px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,255,136,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', top: '-80px', right: '15%',
          width: '350px', height: '350px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <div className="container" style={{ position: 'relative' }}>
          <div style={{ maxWidth: '680px' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(0,255,136,0.06)',
              border: '1px solid rgba(0,255,136,0.2)',
              borderRadius: '20px',
              padding: '6px 14px',
              marginBottom: '24px',
            }}>
              <span className="dot dot-green" style={{ animation: 'pulse 2s infinite' }} />
              <span style={{ fontSize: '12px', color: 'var(--green)', letterSpacing: '1px' }}>
                SYSTEM ONLINE — 247 PRODUCTS IN STOCK
              </span>
            </div>

            <h1 style={{
              fontSize: 'clamp(36px, 5vw, 64px)',
              fontWeight: '900',
              lineHeight: '1.1',
              marginBottom: '20px',
              letterSpacing: '-1px',
            }}>
              <span style={{
                background: 'linear-gradient(135deg, var(--text-1), var(--text-2))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                Elite Hardware
              </span>
              <br />
              <span style={{
                background: 'linear-gradient(135deg, var(--green), var(--cyan))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                For Builders.
              </span>
            </h1>

            <p style={{
              fontSize: '18px',
              color: 'var(--text-2)',
              lineHeight: '1.6',
              marginBottom: '32px',
              maxWidth: '500px',
            }}>
              Premium GPUs, processors, memory, and storage. Sourced direct, shipped fast. No markup. No nonsense.
            </p>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <a href="#products" className="btn btn-primary" style={{ padding: '14px 28px', fontSize: '15px' }}>
                Shop Now →
              </a>
              <a href="/?sale=1" className="btn btn-outline" style={{ padding: '14px 28px', fontSize: '15px' }}>
                🔥 Hot Deals
              </a>
            </div>

            {/* Stats */}
            <div style={{
              display: 'flex',
              gap: '32px',
              marginTop: '44px',
              flexWrap: 'wrap',
            }}>
              {[
                { val: '50K+', label: 'Happy Customers' },
                { val: '99.8%', label: 'Uptime SLA' },
                { val: '4.9★', label: 'Avg. Rating' },
                { val: '24h', label: 'Support' },
              ].map(({ val, label }) => (
                <div key={label}>
                  <div style={{
                    fontSize: '22px',
                    fontWeight: '800',
                    background: 'linear-gradient(135deg, var(--green), var(--cyan))',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}>{val}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-3)', letterSpacing: '0.5px' }}>{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Category filter */}
      <section style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-1)',
        padding: '16px 0',
      }}>
        <div className="container" style={{
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}>
          <span style={{ fontSize: '12px', color: 'var(--text-3)', letterSpacing: '1px', marginRight: '8px' }}>
            FILTER:
          </span>
          <a
            href="/"
            style={{
              padding: '5px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              background: !cat && !sale ? 'rgba(0,255,136,0.12)' : 'var(--bg-2)',
              border: `1px solid ${!cat && !sale ? 'rgba(0,255,136,0.3)' : 'var(--border-b)'}`,
              color: !cat && !sale ? 'var(--green)' : 'var(--text-2)',
              textDecoration: 'none',
              transition: 'var(--transition)',
              letterSpacing: '0.5px',
            }}
          >
            All
          </a>
          {categories.map((c) => (
            <a
              key={c}
              href={`/?cat=${c}`}
              style={{
                padding: '5px 14px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                background: cat === c ? 'rgba(0,255,136,0.12)' : 'var(--bg-2)',
                border: `1px solid ${cat === c ? 'rgba(0,255,136,0.3)' : 'var(--border-b)'}`,
                color: cat === c ? 'var(--green)' : 'var(--text-2)',
                textDecoration: 'none',
                transition: 'var(--transition)',
                letterSpacing: '0.5px',
              }}
            >
              {c}
            </a>
          ))}
          <a
            href="/?sale=1"
            style={{
              padding: '5px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              background: sale ? 'rgba(255,157,0,0.12)' : 'var(--bg-2)',
              border: `1px solid ${sale ? 'rgba(255,157,0,0.3)' : 'var(--border-b)'}`,
              color: sale ? 'var(--orange)' : 'var(--text-2)',
              textDecoration: 'none',
              transition: 'var(--transition)',
              letterSpacing: '0.5px',
            }}
          >
            🔥 On Sale
          </a>
        </div>
      </section>

      {/* Products grid */}
      <section id="products" className="section">
        <div className="container">
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '28px',
          }}>
            <div>
              <h2 style={{ fontSize: '22px', fontWeight: '800', marginBottom: '4px' }}>
                {cat ? `${cat}s` : sale ? '🔥 Hot Deals' : 'All Products'}
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-3)' }}>
                {filtered.length} product{filtered.length !== 1 ? 's' : ''} found
              </p>
            </div>

            <div style={{
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
              fontSize: '12px',
              color: 'var(--text-3)',
            }}>
              <span>Sort:</span>
              <select style={{
                background: 'var(--bg-2)',
                border: '1px solid var(--border-b)',
                borderRadius: '6px',
                padding: '6px 10px',
                color: 'var(--text-2)',
                fontSize: '12px',
                cursor: 'pointer',
              }}>
                <option>Featured</option>
                <option>Price ↑</option>
                <option>Price ↓</option>
                <option>Rating</option>
              </select>
            </div>
          </div>

          {filtered.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '80px 0',
              color: 'var(--text-3)',
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
              <h3 style={{ fontSize: '18px', color: 'var(--text-2)' }}>No products found</h3>
              <a href="/" style={{ color: 'var(--green)', fontSize: '14px' }}>Clear filters</a>
            </div>
          ) : (
            <div className="product-grid">
              {filtered.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Feature banner */}
      <section style={{
        background: 'linear-gradient(135deg, rgba(0,255,136,0.04), rgba(139,92,246,0.04))',
        borderTop: '1px solid var(--border)',
        borderBottom: '1px solid var(--border)',
        padding: '40px 0',
      }}>
        <div className="container">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '24px',
          }}>
            {[
              { icon: '🚀', title: 'Fast Delivery', desc: 'Same-day dispatch for in-stock items' },
              { icon: '🔒', title: 'Secure Checkout', desc: 'Military-grade encryption on all orders' },
              { icon: '↩️', title: '30-Day Returns', desc: 'Hassle-free return policy' },
              { icon: '💬', title: '24/7 Support', desc: 'Expert help whenever you need it' },
            ].map(({ icon, title, desc }) => (
              <div key={title} style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                <span style={{ fontSize: '28px', flexShrink: 0 }}>{icon}</span>
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '4px' }}>{title}</h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-3)' }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
