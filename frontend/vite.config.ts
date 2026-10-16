import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'


export default defineConfig({
  plugins: [
    react(),

    VitePWA({
      registerType: 'autoUpdate',

      includeAssets: [
        'favicon.ico',
        'favicon.svg',
        'apple-touch-icon-180x180.png',
      ],

      manifest: {
        name: 'Field Data Platform',

        short_name: 'FieldData',

        description:
          'Plataforma para captura y sincronización de datos de campo.',

        theme_color: '#0f172a',

        background_color:
          '#f8fafc',

        display: 'standalone',

        start_url: '/',

        scope: '/',

        icons: [
          {
            src:
              'pwa-192x192.png',

            sizes:
              '192x192',

            type:
              'image/png',
          },

          {
            src:
              'pwa-512x512.png',

            sizes:
              '512x512',

            type:
              'image/png',

            purpose:
              'any',
          },

          {
            src:
              'maskable-icon-512x512.png',

            sizes:
              '512x512',

            type:
              'image/png',

            purpose:
              'maskable',
          },
        ],
      },

      workbox: {
        navigateFallback:
          'index.html',

        cleanupOutdatedCaches:
          true,

        globPatterns: [
          '**/*.{js,css,html,ico,png,svg}',
        ],
      },
    }),
  ],
})