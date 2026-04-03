# AGENTS.md

This file provides guidance for agentic coding agents working in this repository.

## Repository Overview

This is the **Pickle Rick** extension for Gemini CLI - a hyper-intelligent autonomous coding agent orchestrator with a TUI interface. The main CLI implementation is in the `cli/` subdirectory.

## Build & Development Commands

```bash
# Navigate to CLI directory
cd cli

# Install dependencies
bun install

# Run in development mode (TUI dashboard)
bun run dev

# Build production executable
bun run build

# Type check without emitting
bun run check

# Run all tests
bun test

# Run single test file
bun test src/path/to/file.test.ts

# Run tests matching a pattern
bun test "SnakeGame"
```

## Code Style Guidelines

### TypeScript & Module System
- **Strict Mode**: All code must use TypeScript with strict mode enabled (see `tsconfig.json`)
- **ESM Modules**: Use ES modules with `.js` extensions for imports (not `.ts`)
- **Bun Runtime**: Code runs on Bun, not Node.js

### Import Organization
Organize imports in this order with blank lines between groups:

```typescript
// 1. Browser/game polyfills (must be first if used)
import { applyPolyfills } from "./games/gameboy/gameboy-polyfills.js";
applyPolyfills();

// 2. Node.js built-ins
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { existsSync } from "node:fs";

// 3. External dependencies
import { Command } from "commander";
import pc from "picocolors";
import { z } from "zod";

// 4. Internal modules (relative imports with .js extension)
import { SessionState } from "./services/config/types.js";
import { GeminiEngine } from "./engines/gemini.js";
```

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `dashboard-controller.ts` |
| Classes | PascalCase | `DashboardController`, `SnakeGame` |
| Functions/Variables | camelCase | `createSession`, `sessionDir` |
| Constants (exported) | UPPER_SNAKE_CASE | `GLOBAL_SESSIONS_DIR` |
| Enums | PascalCase | `Direction.UP` |
| Interfaces | PascalCase (no prefix) | `Point`, `SessionState` |
| Type aliases | PascalCase | `SessionSummary` |

### Type Safety
- **Zod**: Use Zod schemas for all external data validation and JSON parsing
- **Explicit Types**: Always define explicit return types and parameter types
- **Error Types**: Use `unknown` for catch blocks, then narrow with `instanceof`

```typescript
// Good
async function loadState(sessionDir: string): Promise<SessionState | null> {
  try {
    const content = await readFile(path, "utf-8");
    const json = JSON.parse(content);
    return SessionStateSchema.parse(json);
  } catch (e) {
    console.error("Failed to load state:", e);
    return null;
  }
}

// Bad
async function loadState(path) {
  try {
    return JSON.parse(await readFile(path));
  } catch (e) {
    return null;
  }
}
```

### Error Handling Patterns

```typescript
// CLI commands - use picocolors for colored output
try {
  await executor.run();
} catch (err: unknown) {
  const msg = err instanceof Error ? err.message : String(err);
  console.error(pc.red(`💥 Execution failed: ${msg}`));
  process.exit(1);
}

// File operations - wrap with context
try {
  await writeFile(path, content, "utf-8");
} catch (e) {
  throw new Error(`Failed to write state to ${path}: ${e}`);
}
```

### Testing
- **Framework**: Use Bun's built-in test runner (`bun test`)
- **Test Files**: Name test files as `*.test.ts` in the same directory as source
- **Test Setup**: Global mocks are in `src/ui/test-setup.ts` (preloaded via `bunfig.toml`)
- **Structure**: Group tests with `describe()`, use descriptive test names

```typescript
import { expect, test, describe, mock } from "bun:test";

describe("SnakeGame", () => {
  test("should throw on invalid dimensions", () => {
    expect(() => new SnakeGame(5, 5)).toThrow();
  });
});
```

### Code Organization
- **Single Responsibility**: Each file should export one main class/function
- **Barrel Exports**: Use `index.ts` files for clean public APIs
- **Constants**: Define theme and configuration constants in dedicated files (`theme.ts`)
- **Dependencies**: Inject dependencies, avoid global state where possible

### TUI Components (@opentui/core)
- **Renderables**: All UI components extend renderable classes from `@opentui/core`
- **Event Handling**: Use proper event listener patterns with cleanup
- **State Management**: Keep UI state in controller classes, not renderables
- **Theme**: Use centralized theme constants from `./ui/theme.ts`

### Zod Schemas
Define schemas for all persisted state and external data:

```typescript
import { z } from "zod";

export const SessionStateSchema = z.object({
  active: z.boolean(),
  step: z.enum(["prd", "breakdown", "research", "plan", "implement", "refactor", "done"]),
  iteration: z.number(),
  // ...
});

export type SessionState = z.infer<typeof SessionStateSchema>;
```

### Security Best Practices
- **No Secrets**: Never commit API keys, tokens, or sensitive data
- **Input Validation**: Validate all user input with Zod schemas
- **Path Safety**: Validate and sanitize file paths, prevent directory traversal
- **Command Injection**: Use parameterized arrays for exec/spawn commands

### Git & Session Management
- **Worktrees**: Sessions may execute in isolated git worktrees
- **State Persistence**: All state must be serializable to JSON via Zod schemas
- **Cleanup**: Always clean up resources (worktrees, processes, event listeners)
- **Idempotency**: Operations should be safe to retry

## Architecture Reference

### Core Directory Structure
```
cli/
├── src/
│   ├── index.ts              # CLI entry point (Commander.js)
│   ├── games/                # Easter egg games (Snake, Gameboy)
│   ├── services/
│   │   ├── config/           # State management, settings
│   │   ├── execution/        # Sequential executor, prompts
│   │   ├── git/              # Worktrees, diffs, PRs
│   │   └── providers/        # AI provider abstraction (Gemini, Opencode)
│   ├── types/                # Shared type definitions
│   ├── ui/
│   │   ├── components/       # Reusable UI components
│   │   ├── controllers/      # TUI state management
│   │   ├── dialogs/          # Modal dialogs
│   │   ├── views/            # Main view compositions
│   │   ├── theme.ts          # Color palette
│   │   └── test-setup.ts     # Global test mocks
│   └── utils/                # Utility functions
├── package.json
└── tsconfig.json
```

### Task State Machine
The agent progresses through phases: `prd` → `breakdown` → `research/plan/implement/refactor` → `done`

## Common Patterns

### Working with File Paths
```typescript
import { join } from "node:path";
import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";

const sessionDir = join(cwd, ".pickle", "sessions", sessionId);
await mkdir(sessionDir, { recursive: true });
```

### Async File Operations
```typescript
import { readFile, writeFile } from "node:fs/promises";

const content = await readFile(path, "utf-8");
await writeFile(path, JSON.stringify(data, null, 2), "utf-8");
```
