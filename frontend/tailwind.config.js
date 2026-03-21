/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#faf7f0', // Warm ivory
        textPrimary: '#1a1510', // Dark contrast
        textSecondary: '#5a5a5a', // Gray for meta info
        accent: '#111111', 
        skillsBg: '#f2ede0', // Skills section background
        contactBg: '#1a1510', // Contact/Footer dark background
        gridLine: 'rgba(0, 0, 0, 0.04)', 
      },
      fontFamily: {
        sans: ['"Cormorant Garamond"', 'serif'], // Primary UI font
        serif: ['"Playfair Display"', 'serif'], // Large Headers
        mono: ['"DM Mono"', 'monospace'], // Code and Badges
        body: ['"Cormorant Garamond"', 'serif'] 
      },
      backgroundImage: {
        'blueprint': 'linear-gradient(to right, rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.03) 1px, transparent 1px)'
      }
    },
  },
  plugins: [],
}
