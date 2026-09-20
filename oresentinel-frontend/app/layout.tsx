import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OreSentinel — MOIL Limited',
  description:
    'AI-powered insights for a more productive and sustainable tomorrow. Manganese reserve mapping, production forecasting and shortfall prediction for MOIL Limited.',
};

/**
 * Fonts are loaded via <link> rather than next/font/google so that the build
 * never depends on network access to Google Fonts (important for offline/CI builds).
 * Inter = UI typeface, Caveat = the handwritten "Manganese for a stronger India" script.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Caveat:wght@600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans">{children}</body>
    </html>
  );
}
