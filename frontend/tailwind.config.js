/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dnc: {
          blue: "#0A4D98", // DNC brand blue
          gold: "#FFB81C", // DNC brand gold
          light: "#EAF2FA"
        }
      }
    },
  },
  plugins: [],
}
