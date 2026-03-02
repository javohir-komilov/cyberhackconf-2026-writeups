export const products = [
  {
    id: 1,
    name: 'NVIDIA RTX 5090',
    category: 'GPU',
    price: 1999,
    originalPrice: 2199,
    stock: 3,
    rating: 4.9,
    reviews: 214,
    badge: 'HOT',
    badgeType: 'badge-pink',
    specs: ['32GB GDDR7', 'PCIe 5.0 x16', '600W TDP', 'DLSS 4.0'],
    description:
      'The ultimate gaming and AI workload GPU. 32GB of blazing GDDR7 memory with next-gen ray tracing cores.',
    image: '🖥️',
    sku: 'GPU-RTX5090-FE',
  },
  {
    id: 2,
    name: 'AMD Ryzen 9 9950X',
    category: 'CPU',
    price: 699,
    originalPrice: 799,
    stock: 12,
    rating: 4.8,
    reviews: 389,
    badge: 'NEW',
    badgeType: 'badge-green',
    specs: ['16 Cores / 32 Threads', '5.7GHz Boost', '170W TDP', 'AM5 Socket'],
    description:
      'Flagship desktop CPU built on Zen 5 architecture. Dominates in both gaming and content creation.',
    image: '⚙️',
    sku: 'CPU-R9-9950X',
  },
  {
    id: 3,
    name: 'G.Skill Trident Z5 RGB 64GB',
    category: 'RAM',
    price: 299,
    originalPrice: 349,
    stock: 28,
    rating: 4.7,
    reviews: 152,
    badge: 'SALE',
    badgeType: 'badge-orange',
    specs: ['DDR5-7200', 'CL34-45-45-115', 'XMP 3.0', 'RGB Lighting'],
    description:
      'High-frequency DDR5 kit for enthusiast builds. Intel XMP 3.0 and AMD EXPO compatible.',
    image: '💾',
    sku: 'RAM-GSK-TZ5-64',
  },
  {
    id: 4,
    name: 'Samsung 990 Pro 4TB',
    category: 'SSD',
    price: 449,
    originalPrice: 499,
    stock: 45,
    rating: 4.9,
    reviews: 634,
    badge: null,
    badgeType: null,
    specs: ['7,450 MB/s Read', 'PCIe 4.0 NVMe', 'M.2 2280', '1.2PBW Endurance'],
    description:
      'Professional-grade NVMe SSD with blazing sequential read speeds and exceptional longevity.',
    image: '🗄️',
    sku: 'SSD-990PRO-4TB',
  },
  {
    id: 5,
    name: 'LG UltraGear 4K 240Hz',
    category: 'Monitor',
    price: 899,
    originalPrice: 999,
    stock: 7,
    rating: 4.8,
    reviews: 421,
    badge: 'POPULAR',
    badgeType: 'badge-purple',
    specs: ['27" OLED', '3840×2160', '0.03ms GtG', 'HDMI 2.1 / DP 2.0'],
    description:
      'Stunning 4K OLED gaming monitor with near-instant response time and perfect blacks.',
    image: '🖥️',
    sku: 'MON-LG-27GR85U',
  },
  {
    id: 6,
    name: 'Intel Arc B580 XT',
    category: 'GPU',
    price: 279,
    originalPrice: 299,
    stock: 19,
    rating: 4.6,
    reviews: 88,
    badge: 'VALUE',
    badgeType: 'badge-green',
    specs: ['12GB GDDR6', 'PCIe 4.0 x8', '190W TDP', 'XeSS 2.0'],
    description:
      'Best-in-class budget GPU with 12GB VRAM. Exceptional rasterization and AI upscaling.',
    image: '🎮',
    sku: 'GPU-ARC-B580XT',
  },
  {
    id: 7,
    name: 'Corsair HX1500i PSU',
    category: 'PSU',
    price: 299,
    originalPrice: 349,
    stock: 22,
    rating: 4.9,
    reviews: 317,
    badge: null,
    badgeType: null,
    specs: ['1500W Output', '80+ Platinum', 'Fully Modular', 'ATX 3.0'],
    description:
      'Premium fully modular power supply with digital monitoring and 10-year warranty.',
    image: '⚡',
    sku: 'PSU-CRS-HX1500I',
  },
  {
    id: 8,
    name: 'ASUS ROG Maximus Z890',
    category: 'Motherboard',
    price: 699,
    originalPrice: 799,
    stock: 6,
    rating: 4.8,
    reviews: 73,
    badge: 'PRO',
    badgeType: 'badge-purple',
    specs: ['LGA 1851', 'DDR5 Support', 'PCIe 5.0 x16', '10Gb LAN'],
    description:
      'Flagship Z890 motherboard for Intel Core Ultra 200 series. Extreme overclocking support.',
    image: '🔧',
    sku: 'MB-ASUS-ROG-Z890',
  },
];

export function getProduct(id) {
  return products.find((p) => p.id === parseInt(id)) || null;
}

export function getRelated(id, limit = 3) {
  const product = getProduct(id);
  if (!product) return [];
  return products
    .filter((p) => p.id !== product.id && p.category !== product.category)
    .slice(0, limit);
}
