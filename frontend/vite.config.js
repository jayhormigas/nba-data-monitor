// Vite is the build tool that runs the React dev server and bundles the
// app for production. This config just enables React support and sets the
// dev server to run on port 3000.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `command` is "serve" for the local dev server and "build" for a production
// build. On GitHub Pages the site is served from a subfolder that matches the
// repo name (https://<user>.github.io/nba-data-monitor/), so the built assets
// must be prefixed with "/nba-data-monitor/". Locally we keep it at "/".
// NOTE: if you name your GitHub repo something other than "nba-data-monitor",
// change the string below to "/<your-repo-name>/".
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === "build" ? "/nba-data-monitor/" : "/",
  server: { port: 3000 },
}));
