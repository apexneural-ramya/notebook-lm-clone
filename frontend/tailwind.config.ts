import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0A0A0A',
        foreground: '#f1f5f9',
        primary: {
          DEFAULT: '#DC2626',
          hover: '#B91C1C',
        },
        secondary: {
          DEFAULT: '#1F1F1F',
          light: '#2A2A2A',
        },
        accent: {
          DEFAULT: '#EF4444',
          dark: '#DC2626',
        },
        speaker1: {
          DEFAULT: '#DC2626',
          light: '#7F1D1D',
        },
        speaker2: {
          DEFAULT: '#991B1B',
          light: '#5C1A1A',
        },
      },
    },
  },
  plugins: [],
}
export default config

