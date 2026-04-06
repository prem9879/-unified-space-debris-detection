export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        heading: ["Space Grotesk", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"]
      },
      colors: {
        obsidian: "#0a0f1a",
        storm: "#12233f",
        signal: "#39d2ff",
        alert: "#ff6d4d"
      }
    }
  },
  plugins: []
};
