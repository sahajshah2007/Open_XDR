/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b1018',
        panel: '#131c28',
        primary: '#e8b45b',
        secondary: '#8caecc',
        danger: '#e47c79',
        warning: '#e3a75f',
        success: '#88cbb1',
        textMain: '#e5ebef',
        textMuted: '#93a1b2'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
