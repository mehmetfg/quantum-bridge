/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Boru hattındaki üç taraf, arayüz boyunca hep aynı renkle gösterilir.
        klasik: { DEFAULT: '#38bdf8', dark: '#0284c7' },
        yapayzeka: { DEFAULT: '#a78bfa', dark: '#7c3aed' },
        kuantum: { DEFAULT: '#34d399', dark: '#059669' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      keyframes: {
        pulseRing: {
          '0%': { transform: 'scale(0.9)', opacity: '0.7' },
          '70%': { transform: 'scale(1.3)', opacity: '0' },
          '100%': { transform: 'scale(1.3)', opacity: '0' },
        },
        slideIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        pulseRing: 'pulseRing 1.6s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        slideIn: 'slideIn 0.35s ease-out',
      },
    },
  },
  plugins: [],
};
