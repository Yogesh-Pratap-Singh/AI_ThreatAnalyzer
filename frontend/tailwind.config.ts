import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Accessibility-compliant dark-theme color tokens for threat severity
        critical: { 
          DEFAULT: "#ef4444", 
          bg: "#450a0a",      // Dark red background
          border: "#991b1b",  // Medium red border
          text: "#fca5a5"     // Light red text
        },
        high: { 
          DEFAULT: "#f97316", 
          bg: "#431407",      // Dark orange bg
          border: "#9a3412",  // Medium orange border
          text: "#fed7aa"     // Light orange text
        },
        medium: { 
          DEFAULT: "#eab308", 
          bg: "#422006",      // Dark yellow bg
          border: "#854d0e",  // Medium yellow border
          text: "#fef08a"     // Light yellow text
        },
        low: { 
          DEFAULT: "#22c55e", 
          bg: "#062f4f",      // Dark green bg (adjusted contrast)
          border: "#166534",  // Medium green border
          text: "#bbf7d0"     // Light green text
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 200ms ease-in-out",
        "slide-up": "slideUp 250ms ease-out",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { transform: "translateY(8px)", opacity: "0" }, to: { transform: "translateY(0)", opacity: "1" } },
      },
    },
  },
  plugins: [],
};
export default config;
