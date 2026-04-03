# AGENTS.md

This file provides guidance for agentic coding agents working in this repository.

## Repository Overview

This is the **Pickle Rick** extension for Gemini CLI - a hyper-intelligent autonomous coding agent orchestrator with a TUI interface. The main CLI implementation is in the `cli/` subdirectory.

## Build & Development Commands

### CLI (primary workspace)
```bash
cd cli

bun install              # Install dependencies
bun run dev              # Run TUI dashboard in dev mode
bun run build            # Build production binary
bun run check            # Type check (tsc --noEmit)
bun test                 # Run all tests
bun test src/path/to/file.test.ts   # Run a single test file
bun test "SnakeGame"     # Run tests matching a pattern
```

### Extension
```bash
cd extension
npm run lint:fix         # Lint and auto-fix
npm run format           # Format code
npm test                 # Run extension tests
npm run build            # Build extension
```

### Pre-commit Hook
Runs `npx lint-staged` on `extension/src/**/*.ts` (eslint --fix + prettier --write) then `cd extension && npm test && npm run build`.

## Code Style Guidelines

### TypeScript & Module System
- **Strict Mode**: `strict: true` in tsconfig, target ESNext, module ESNext, moduleResolution bundler
- **ESM Modules**: Use ES modules with `.js` extensions for relative imports (not `.ts`)
- **Bun Runtime**: Code runs on Bun, not Node.js. Use `@types/bun` for types.

### Import Organization
```typescript
// 1. Polyfills (if used)
import { applyPolyfills } from "./games/gameboy/gameboy-polyfills.js";
applyPolyfills();

// 2. Node.js built-ins
import { readFile } from "node:fs/promises";
import { join } from "node:path";

// 3. External dependencies
import { Command } from "commander";
import pc from "picocolors";
import { z } from "zod";

// 4. Internal modules (relative, .js extension)
import { SessionState } from "./services/config/types.js";
```

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `dashboard-controller.ts` |
| Classes | PascalCase | `DashboardController` |
| Functions/Variables | camelCase | `createSession` |
| Constants (exported) | UPPER_SNAKE_CASE | `GLOBAL_SESSIONS_DIR` |
| Enums/Interfaces/Types | PascalCase | `Direction`, `Point` |

### Type Safety
- **Zod**: Use Zod schemas for all external data validation and persisted state
- **Explicit Types**: Always define explicit return types and parameter types
- **Error Types**: Use `unknown` for catch blocks, narrow with `instanceof`

### Error Handling
```typescript
// CLI commands - use picocolors for colored output
try {
  await executor.run();
} catch (err: unknown) {
  const msg = err instanceof Error ? err.message : String(err);
  console.error(pc.red(`Execution failed: ${msg}`));
  process.exit(1);
}
```

### Testing
- **Framework**: Bun's built-in test runner (`bun:test`) for CLI; Vitest for extension
- **Files**: `*.test.ts` co-located with source
- **Setup**: Global mocks in `src/ui/test-setup.ts` (preloaded via `bunfig.toml`)
```typescript
import { expect, test, describe } from "bun:test";

describe("SnakeGame", () => {
  test("should throw on invalid dimensions", () => {
    expect(() => new SnakeGame(5, 5)).toThrow();
  });
});
```

### Code Organization
- Single responsibility per file; barrel exports via `index.ts`
- Inject dependencies, avoid global state
- TUI components extend `@opentui/core` renderables; keep UI state in controllers
- Theme constants in `./ui/theme.ts`

### Security & Git
- Never commit secrets; validate all input with Zod
- Sessions run in isolated git worktrees; clean up resources after use
- All state must be serializable to JSON via Zod schemas; operations should be idempotent

## Architecture

```
cli/src/
├── index.ts              # CLI entry point (Commander)
├── games/                # Easter egg games
├── skills/               # Agent skill prompts (markdown)
├── services/
│   ├── commands/         # CLI command handlers
│   ├── config/           # State management, settings
│   ├── execution/        # Sequential executor, prompts, worker
│   ├── git/              # Worktrees, diffs, PRs
│   └── providers/        # AI provider abstraction
├── types/                # Shared type definitions
├── ui/
│   ├── components/       # Reusable UI
│   ├── controllers/      # TUI state management
│   ├── dialogs/          # Modal dialogs
│   ├── views/            # Main view compositions
│   └── theme.ts          # Color palette
└── utils/
```

Task state machine: `prd` → `breakdown` → `research/plan/implement/refactor` → `done`
