import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/favicon-32.png", "icons/apple-touch-icon.png"],
      manifest: {
        name: "Simulafoot",
        short_name: "Simulafoot",
        description: "Simulateur de football complet",
        lang: "fr",
        start_url: "/",
        display: "standalone",
        orientation: "landscape",
        background_color: "#0B0E14",
        theme_color: "#0B0E14",
        icons: [
          { src: "icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "icons/icon-512-maskable.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        // Référence peu changeante (championnats, vivier de clubs) : mise en
        // cache réseau-d'abord. Les POST de simulation ne sont jamais mis en
        // cache par Workbox par défaut (seules les requêtes GET le sont).
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith("/api/leagues") || url.pathname.startsWith("/api/clubs"),
            handler: "NetworkFirst",
            options: { cacheName: "api-reference-data", expiration: { maxEntries: 20, maxAgeSeconds: 3600 } },
          },
        ],
      },
    }),
  ],
  server: {
    // host: true -- équivalent de --host 0.0.0.0, indispensable pour tester
    // depuis le téléphone via l'IP locale du PC.
    host: true,
    // Vite rejette par défaut toute requête dont l'en-tête Host n'est pas
    // reconnu (protection anti DNS-rebinding) -- bloque donc l'accès via un
    // tunnel public (ex. trycloudflare.com), dont le sous-domaine change à
    // chaque lancement. `true` désactive cette vérification -- acceptable
    // ici (dev local temporaire), à ne pas garder tel quel pour un vrai
    // déploiement.
    allowedHosts: true,
  },
});
