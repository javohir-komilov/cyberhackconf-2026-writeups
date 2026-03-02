import './globals.css';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'TechMart — Elite Hardware Store',
  description: 'Premium PC hardware: GPUs, CPUs, RAM, Storage and more. Fast shipping, competitive prices.',
  keywords: 'GPU, CPU, RAM, SSD, PC hardware, gaming, workstation',
  generator: 'Next.js 15.0.0',
  other: {
    'x-build-info': 'Next.js 15.0.0 | React 19.0.0 | RSC enabled',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      {/*
        Build info: Next.js 15.0.0 | React 19.0.0 | RSC enabled
        Infrastructure: Node.js 20 | SecureShield WAF v2.1.4
        TODO: upgrade SecureShield WAF rules before next release
      */}
      <body className="scanlines">
        <div className="page-wrapper">
          <Header />
          <main style={{ flex: 1 }}>
            {children}
          </main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
