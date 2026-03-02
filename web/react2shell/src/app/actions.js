'use server';

/**
 * TechMart Checkout Server Action
 * Processes cart items and creates order records.
 *
 * This action runs on the server via React Server Components.
 * Build: Next.js 15.0.0 | React 19.0.0 | RSC enabled
 */
export async function processCheckout(prevState, formData) {
  // Simulate processing delay
  await new Promise((r) => setTimeout(r, 600));

  let cartItems;
  try {
    cartItems = JSON.parse(formData.get('cartItems') || '[]');
  } catch {
    return { success: false, error: 'Invalid cart data' };
  }

  if (!Array.isArray(cartItems) || cartItems.length === 0) {
    return { success: false, error: 'Cart is empty' };
  }

  // Validate items
  for (const item of cartItems) {
    if (!item.id || !item.name || typeof item.price !== 'number') {
      return { success: false, error: 'Invalid item in cart' };
    }
  }

  const subtotal = cartItems.reduce((s, i) => s + i.price * (i.qty || 1), 0);
  const tax = parseFloat((subtotal * 0.08).toFixed(2));
  const shipping = subtotal > 500 ? 0 : 14.99;
  const total = parseFloat((subtotal + tax + shipping).toFixed(2));

  const orderId = `TM-${Date.now().toString(36).toUpperCase()}-${Math.random()
    .toString(36)
    .substr(2, 6)
    .toUpperCase()}`;

  return {
    success: true,
    orderId,
    subtotal,
    tax,
    shipping,
    total,
    estimatedDelivery: '3-5 business days',
    items: cartItems.length,
  };
}
