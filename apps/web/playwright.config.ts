import { defineConfig, devices } from "@playwright/test";

/**
 * E2E do fluxo principal. Sobe o front como no CLAUDE.md (`npm run dev:web`, porta 3000).
 * A API (NEXT_PUBLIC_API_URL, padrão http://localhost:8000) e o banco semeado (ver
 * docs/spec-gaps.md, "Semente do e2e") precisam estar de pé: o e2e testa a integração de verdade.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"], ["junit", { outputFile: "e2e-results.xml" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  // Mobile-first: o usuário real está no celular, só com toques.
  projects: [{ name: "mobile-chromium", use: { ...devices["Pixel 5"] } }],
  webServer: {
    command: "npm run dev:web",
    cwd: "../..",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
