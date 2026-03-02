import { getProduct, getRelated } from '@/lib/products';
import ProductCard from '@/components/ProductCard';
import AddToCartButton from '@/components/AddToCartButton';
import { notFound } from 'next/navigation';
import Link from 'next/link';

export async function generateStaticParams() {
  const { products } = await import('@/lib/products');
  return products.map((p) => ({ id: String(p.id) }));
}

export async function generateMetadata({ params }) {
  const product = getProduct((await params).id);
  if (!product) return { title: 'Not Found' };
  return {
    title: `${product.name} — TechMart`,
    description: product.description,
  };
}

export default async function ProductPage({ params }) {
  const product = getProduct((await params).id);
  if (!product) notFound();

  const related = getRelated((await params).id);
  const discount = product.originalPrice
    ? Math.round((1 - product.price / product.originalPrice) * 100)
    : 0;

  return (
    <>
      {/* Breadcrumb */}
      <div style={{
        background: 'var(--bg-1)',
        borderBottom: '1px solid var(--border)',
        padding: '12px 0',
      }}>
        <div className="container" style={{ padding: '0 24px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-3)' }}>
            <Link href="/" style={{ color: 'var(--text-3)' }}>Home</Link>
            {' › '}
            <Link href={`/?cat=${product.category}`} style={{ color: 'var(--text-3)' }}>
              {product.category}
            </Link>
            {' › '}
            <span style={{ color: 'var(--text-2)' }}>{product.name}</span>
          </p>
        </div>
      </div>

      <div className="section">
        <div className="container">
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '48px',
            alignItems: 'start',
            marginBottom: '64px',
          }}>
            {/* Product image */}
            <div>
              <div style={{
                background: 'linear-gradient(135deg, var(--bg-2), var(--bg-3))',
                border: '1px solid var(--border)',
                borderRadius: '20px',
                padding: '80px 40px',
                textAlign: 'center',
                fontSize: '120px',
                lineHeight: 1,
                marginBottom: '16px',
                position: 'relative',
              }}>
                {product.image}
                {product.badge && (
                  <div style={{ position: 'absolute', top: '20px', left: '20px' }}>
                    <span className={`badge ${product.badgeType}`}>{product.badge}</span>
                  </div>
                )}
              </div>

              {/* Thumbnails */}
              <div style={{ display: 'flex', gap: '8px' }}>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} style={{
                    flex: 1,
                    height: '70px',
                    background: 'var(--bg-2)',
                    border: `1px solid ${i === 1 ? 'var(--green)' : 'var(--border)'}`,
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px',
                    cursor: 'pointer',
                    opacity: i === 1 ? 1 : 0.4,
                  }}>
                    {product.image}
                  </div>
                ))}
              </div>
            </div>

            {/* Product details */}
            <div>
              <div style={{ marginBottom: '6px' }}>
                <span style={{
                  fontSize: '11px',
                  color: 'var(--purple)',
                  letterSpacing: '2px',
                  textTransform: 'uppercase',
                }}>
                  {product.category}
                </span>
              </div>

              <h1 style={{
                fontSize: '28px',
                fontWeight: '800',
                lineHeight: '1.2',
                marginBottom: '12px',
              }}>
                {product.name}
              </h1>

              {/* Rating */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                marginBottom: '20px',
              }}>
                <div style={{ display: 'flex', gap: '2px' }}>
                  {[1,2,3,4,5].map((s) => (
                    <span key={s} style={{
                      fontSize: '16px',
                      color: s <= Math.round(product.rating) ? 'var(--orange)' : 'var(--text-4)',
                    }}>★</span>
                  ))}
                </div>
                <span style={{ fontSize: '14px', color: 'var(--text-2)' }}>
                  {product.rating} · {product.reviews} reviews
                </span>
                <span style={{
                  fontSize: '11px',
                  color: 'var(--green)',
                  background: 'rgba(0,255,136,0.08)',
                  border: '1px solid rgba(0,255,136,0.2)',
                  borderRadius: '4px',
                  padding: '2px 6px',
                }}>Verified</span>
              </div>

              {/* Price */}
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '24px',
              }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '8px' }}>
                  <div className="price" style={{ fontSize: '32px' }}>
                    ${product.price.toLocaleString()}
                  </div>
                  {product.originalPrice && (
                    <>
                      <div style={{
                        fontSize: '18px',
                        color: 'var(--text-3)',
                        textDecoration: 'line-through',
                      }}>
                        ${product.originalPrice.toLocaleString()}
                      </div>
                      <span className="badge badge-orange">SAVE {discount}%</span>
                    </>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {product.stock > 5 ? (
                    <>
                      <span className="dot dot-green" />
                      <span style={{ fontSize: '13px', color: 'var(--green)' }}>
                        In Stock ({product.stock} units)
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="dot dot-orange" />
                      <span style={{ fontSize: '13px', color: 'var(--orange)' }}>
                        Only {product.stock} left!
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Specs */}
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{
                  fontSize: '12px',
                  letterSpacing: '2px',
                  textTransform: 'uppercase',
                  color: 'var(--text-3)',
                  marginBottom: '12px',
                }}>Key Specs</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '8px',
                }}>
                  {product.specs.map((spec) => (
                    <div key={spec} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'var(--bg-2)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      padding: '8px 12px',
                    }}>
                      <span style={{ color: 'var(--cyan)', fontSize: '12px' }}>◈</span>
                      <span style={{ fontSize: '13px', color: 'var(--text-2)' }}>{spec}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Description */}
              <p style={{
                color: 'var(--text-2)',
                lineHeight: '1.7',
                fontSize: '14px',
                marginBottom: '24px',
                padding: '16px',
                background: 'var(--bg-2)',
                borderRadius: '10px',
                borderLeft: '3px solid var(--purple)',
              }}>
                {product.description}
              </p>

              {/* SKU */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '12px',
                color: 'var(--text-3)',
                fontFamily: 'monospace',
                marginBottom: '20px',
              }}>
                <span>SKU: {product.sku}</span>
                <span>Category: {product.category}</span>
              </div>

              {/* CTA */}
              <div style={{ display: 'flex', gap: '12px' }}>
                <AddToCartButton product={product} />
                <Link
                  href="/cart"
                  className="btn btn-outline"
                  style={{ flex: 1, justifyContent: 'center', display: 'flex' }}
                >
                  🛒 View Cart
                </Link>
              </div>
            </div>
          </div>

          {/* Related products */}
          {related.length > 0 && (
            <div>
              <h2 style={{
                fontSize: '20px',
                fontWeight: '700',
                marginBottom: '20px',
                paddingTop: '40px',
                borderTop: '1px solid var(--border)',
              }}>
                You Might Also Like
              </h2>
              <div className="product-grid">
                {related.map((p) => (
                  <ProductCard key={p.id} product={p} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
