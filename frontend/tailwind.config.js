/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f7f4",
          100: "#dceee6",
          600: "#1a6b4a",
          700: "#145538",
          800: "#0f3f2a",
        },
      },
    },
  },
  plugins: [],
};
