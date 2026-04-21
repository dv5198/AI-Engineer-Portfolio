/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: '#f0ebe0',
        ivoryDeep: '#e8e0d0',
        ivoryDark: '#ddd4c0',
        warmBrown: '#4a3a28',
        warmMid: '#7a6a55',
        warmLight: '#a09878',
        accent: '#b89868',
        accentDeep: '#8a6a45',
        background: '#f0ebe0', // Updated from #faf7f0
        textPrimary: '#1a1510', 
        textSecondary: '#5a5a5a', 
        skillsBg: '#e8e0d0', // Updated from #f2ede0
        contactBg: '#1a1510', 
        gridLine: 'rgba(0, 0, 0, 0.04)', 
      },
      fontFamily: {
        sans: ['"Cormorant Garamond"', 'serif'], // Primary UI font
        serif: ['"Cormorant Garamond"', 'serif'], // Large Headers
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
