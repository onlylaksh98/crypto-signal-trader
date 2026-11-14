/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Dark navy base palette
        navy: {
          950: '#030712',
          900: '#0a0f1e',
          800: '#0d1526',
          700: '#111d35',
          600: '#162545',
          500: '#1e3058',
        },
        // Accent cyan-blue
        accent: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          muted: '#1d4ed8',
          glow: 'rgba(59,130,246,0.15)',
        },
        // P&L colours
        profit: {
          DEFAULT: '#10b981',
          muted: '#064e3b',
          text: '#34d399',
        },
        loss: {
          DEFAULT: '#ef4444',
          muted: '#7f1d1d',
          text: '#f87171',
        },
        warn: {
          DEFAULT: '#f59e0b',
          muted: '#78350f',
        },
        // UI surface
        surface: {
          DEFAULT: '#111827',
          raised: '#1f2937',
          overlay: '#374151',
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.06)',
          accent: 'rgba(59,130,246,0.3)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-up': 'slideUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(59,130,246,0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(59,130,246,0.6)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'card-glow': 'linear-gradient(135deg, rgba(59,130,246,0.05) 0%, transparent 60%)',
      },
    },
  },
  plugins: [],
}
