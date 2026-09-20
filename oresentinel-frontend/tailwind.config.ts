import type { Config } from 'tailwindcss';

/**
 * Design tokens transcribed from the OreSentinel mockup.
 * Keep these in one place so every widget stays visually consistent.
 */
const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Sidebar / brand
        ink: {
          DEFAULT: '#0B2523', // sidebar background
          deep: '#081E1C',    // sidebar footer card + promo fallback
          hover: '#123935',   // nav item hover
          active: '#15453F',  // nav item active
        },
        brand: {
          DEFAULT: '#106D63', // primary accent (icons, buttons)
          mid: '#3C9A8E',     // forecast line / secondary accent
          light: '#DCF0EC',
        },
        canvas: '#F3F6F6',    // main content background
        line: '#E2E8F0',      // card borders + grid lines
        actual: '#0F6CBD',    // "Actual Production" line
        target: '#A0AEC0',    // "Target" line
        risk: {
          high: '#E53E3E',
          highBg: '#FED7D7',
          med: '#DD6B20',
          medBg: '#FEEBC8',
          low: '#3182CE',
          lowBg: '#EBF8FF',
          ok: '#2F855A',
          okBg: '#E6FFEC',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
        script: ['Caveat', 'Rochester', 'cursive'],
      },
      borderRadius: { xl: '12px', '2xl': '16px' },
      boxShadow: {
        card: '0 1px 2px 0 rgb(16 24 40 / 0.04), 0 1px 3px 0 rgb(16 24 40 / 0.06)',
      },
      keyframes: {
        'fade-up': { '0%': { opacity: '0', transform: 'translateY(4px)' }, '100%': { opacity: '1', transform: 'none' } },
      },
      animation: { 'fade-up': 'fade-up .25s ease-out both' },
    },
  },
  plugins: [],
};
export default config;
