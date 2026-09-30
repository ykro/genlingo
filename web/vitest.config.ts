import { defineConfig } from "vitest/config";

// Unit tests run everywhere; rules tests need the Firestore emulator (npm run test:rules).
export default defineConfig({
  test: { include: ["tests/**/*.test.ts"], exclude: ["tests/rules/**", "node_modules/**"] },
});
