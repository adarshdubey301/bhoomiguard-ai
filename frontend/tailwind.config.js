/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        slate: {
          50: 'var(--c-slate-50)',
          100: 'var(--c-slate-100)',
          200: 'var(--c-slate-200)',
          300: 'var(--c-slate-300)',
          400: 'var(--c-slate-400)',
          500: 'var(--c-slate-500)',
          600: 'var(--c-slate-600)',
          700: 'var(--c-slate-700)',
          800: 'var(--c-slate-800)',
          900: 'var(--c-slate-900)',
        },
        surface: 'var(--c-surface)',
        card: 'var(--c-card)',
        border: 'var(--c-border)',
      }
    },
  },
  plugins: [],
}
