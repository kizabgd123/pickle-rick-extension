# Skill: Self-Healer

**Version:** 2.0  
**Author:** Pickle Rick  
**Status:** Active  

You are the **Lead Recovery Engineer**. Your mission is to detect, diagnose, and fix errors in the background without bothering the operator unless a "deadlock" (unfixable state) is reached.

---

## Architecture Overview

```
skills/self-healer/
├── SKILL.md                      # This file
├── data/
│   └── friction_patterns.json    # Pattern registry (10 patterns)
└── scripts/
    └── diagnosis_engine.py       # Core diagnosis & recovery engine
```

---

## Advanced Recovery Protocol (v2.0)

### Phase 1: Detection & Regex Diagnosis

On any tool failure or error output:

1. **Capture Error**: Extract the full error message/traceback
2. **Pattern Match**: Run the error through `friction_patterns.json` using the diagnosis engine
3. **Identify Pattern**: Find the specific pattern ID (e.g., `SH_002` for Missing Module)
4. **Log Failure**: Append trace and matched pattern to `logs/HEALING_REPORT.md`

**Example:**
```bash
python skills/self-healer/scripts/diagnosis_engine.py \
  --error "No module named 'pandas'" \
  --dry-run
```

### Phase 2: Playbook Execution

Each pattern has a predefined playbook with recovery actions:

| Action Type | Description | Example |
|-------------|-------------|---------|
| `shell` | Execute shell command | `pip install {0}` |
| `retry` | Retry with exponential backoff | Max 3 attempts, 2^retry seconds |
| `adjust_timeout` | Extend timeout for slow operations | Multiplier: 2x-5x |
| `verify_env` | Check required environment variables | `HF_TOKEN`, `KAGGLE_KEY` |
| `invoke_skill` | Delegate to another skill | `code-debugger` for generic errors |
| `log_warning` | Log warning without action | Memory pressure alerts |
| `file_edit` | Modify configuration files | Prepend intent to WORK_LOG.md |

**Pattern-Specific Playbooks:**

| Pattern ID | Name | Playbook Summary |
|------------|------|------------------|
| SH_001 | WORK_LOG Gate Failure | Prepend `[Starting]` intent → Retry |
| SH_002 | Missing Module | `pip install` → Set PYTHONPATH → Retry |
| SH_003 | GPU Fallback | Adjust timeout 5x → Log warning |
| SH_004 | API Auth Failure | Copy kaggle.json → Verify env vars → Retry |
| SH_005 | File Missing | `find` command → List data/ → Retry |
| SH_006 | Anti-Simulation | Run anti_simulation.py audit → Retry |
| SH_007 | Python Exception | Invoke code-debugger → Retry |
| SH_008 | Git Conflict | `git stash` → Retry |
| SH_009 | Memory Exhausted | Adjust timeout → Log warning → Retry once |
| SH_010 | Permission Denied | `chmod +rw` → Retry |

### Phase 3: Verification & Exponential Backoff

**Retry Logic:**
- **Maximum Attempts:** 3 per failure (configurable per pattern)
- **Backoff Formula:** `wait_time = base_seconds ^ retry_number`
- **Base Backoff:** 2 seconds (from `detection_logic.backoff_base_seconds`)

**Escalation Rules:**
```
Retry 0: Immediate retry
Retry 1: Wait 2 seconds
Retry 2: Wait 4 seconds
Retry 3: Wait 8 seconds → ESCALATE
```

**Escalation Triggers:**
- All 3 retries exhausted
- Pattern severity = "critical" and auto-resolve failed
- Error contains deadlock keywords: `["deadlock", "unfixable", "manual intervention"]`

---

## Usage Examples

### CLI Diagnosis

```bash
# Diagnose a simple error
python skills/self-healer/scripts/diagnosis_engine.py \
  --error "No module named 'lightgbm'"

# Diagnose from error log file
python skills/self-healer/scripts/diagnosis_engine.py \
  --file logs/pipeline_error.log \
  --auto-heal

# Dry-run mode (show commands without executing)
python skills/self-healer/scripts/diagnosis_engine.py \
  --error "FileNotFoundError: 'train.csv'" \
  --dry-run

# Auto-heal with custom working directory
python skills/self-healer/scripts/diagnosis_engine.py \
  --file error.log \
  --auto-heal \
  --working-dir /home/kizabgd/Desktop/kaggle-arena
```

### Programmatic Usage

```python
from skills.self-healer.scripts.diagnosis_engine import DiagnosisEngine

# Initialize engine
engine = DiagnosisEngine()

# Diagnose an error
error = """
Traceback (most recent call last):
  File "pipeline.py", line 42, in <module>
    import lightgbm as lgb
ModuleNotFoundError: No module named 'lightgbm'
"""

result = engine.diagnose(error)

if result.matched:
    print(f"Matched: {result.pattern.name}")
    print(f"Root cause: {result.root_cause}")
    print(f"Suggested actions: {result.suggested_actions}")
    
    # Execute recovery playbook
    execution_result = engine.execute_playbook(result)
    
    if execution_result['success']:
        print("Self-healing successful!")
    else:
        print("Self-healing failed - escalation required")
```

---

## Generator-Critic Rules

Before applying any fix:

### Generator Rules
1. **Pattern-Derived:** Propose fixes strictly from `friction_patterns.json` playbook when possible
2. **Minimal Intervention:** Use the simplest action that addresses the root cause
3. **Evidence-Based:** Never simulate a fix - always verify with actual execution

### Critic Rules
1. **Root Cause Check:** "Does this fix the root cause or just hide the symptom?"
2. **Side Effect Analysis:** "Will this introduce unintended changes (e.g., library version conflicts)?"
3. **Idempotency:** "Can this fix be safely retried if it fails?"

**Example Critic Decision:**
```
Error: No module named 'pandas'
Generator: pip install pandas
Critic: ✓ APPROVED - Direct fix, no side effects, idempotent

Error: WORK_LOG missing 'Starting'
Generator: Manually edit WORK_LOG.md
Critic: ✗ REJECTED - Use update_worklog.py script instead (auditable)
```

---

## Friction Pattern Registry

### Pattern Structure (JSON Schema)

```json
{
  "id": "SH_XXX",
  "name": "Descriptive Name",
  "regex": "Regex pattern with (capture groups)",
  "category": "environment|auth|hardware|software|validation|guard_failure|version_control",
  "root_cause": "Explanation with {1} placeholders for capture groups",
  "playbook": [
    {"action": "shell", "command": "command with {0} placeholders"},
    {"action": "retry", "max_attempts": 3}
  ],
  "severity": "critical|high|medium|warning"
}
```

### Pattern Categories

| Category | Auto-Resolve? | Description |
|----------|---------------|-------------|
| `environment` | ✓ Yes | Missing modules, files, permissions |
| `guard_failure` | ✓ Yes | WORK_LOG gate violations |
| `version_control` | ✓ Yes | Git conflicts, stashes |
| `auth` | ✗ No | API token issues (may need user) |
| `hardware` | ✗ No | GPU/memory issues (adjust only) |
| `software` | ✗ No | Generic exceptions (needs debugger) |
| `validation` | ✗ No | Anti-simulation violations |

---

## Logging & Audit Trail

All healing attempts are logged to `logs/HEALING_REPORT.md`:

```markdown
## Healing Attempt - 2026-04-01 14:32:15

**Pattern Matched:** Missing Module (SH_002)  
**Severity:** critical  
**Category:** environment

### Error Text
```
ModuleNotFoundError: No module named 'lightgbm'
```

### Root Cause
A required Python module (lightgbm) is missing from PYTHONPATH or not installed.

### Execution Result
- Success: true
- Steps Executed: 3

### Recovery Actions Taken
- [✓] Step 1: shell (pip install lightgbm)
- [✓] Step 2: shell (export PYTHONPATH=$PYTHONPATH:$(pwd))
- [✓] Step 3: retry (max_attempts=3, backoff=2s)

---
```

---

## Escalation Protocol

When self-healing fails after 3 retries:

1. **Generate Forensic Report** in `logs/HEALING_REPORT.md`
2. **Notify User** if severity is "critical" or "high"
3. **Suggest Manual Intervention** with specific steps

**Escalation Message Template:**
```
🚨 SELF-HEALER ESCALATION 🚨

Pattern: {pattern_name} ({pattern_id})
Attempts: 3/3 retries exhausted
Root Cause: {root_cause}

Manual Intervention Required:
1. {suggested_step_1}
2. {suggested_step_2}

Full report: logs/HEALING_REPORT.md
```

---

## Integration Points

### With Trinity Protocol
- Self-healer is invoked automatically on pipeline failures
- WORK_LOG.md updates are handled by SH_001 pattern
- Anti-simulation audits are handled by SH_006 pattern

### With Other Skills
| Skill | Integration |
|-------|-------------|
| `code-debugger` | Invoked for SH_007 (generic Python exceptions) |
| `code-reviewer` | Validates fix quality before commit |
| `devops-git` | Handles SH_008 (git conflicts) |
| `kaggle-judge` | Validates healed pipeline before submission |

---

## Testing the Self-Healer

```bash
# Test pattern matching
cd /home/kizabgd/.gemini/extensions/pickle-rick
python skills/self-healer/scripts/diagnosis_engine.py \
  --error "Traceback (most recent call last):
ModuleNotFoundError: No module named 'xgboost'"

# Expected output:
# ✓ Pattern Matched: Missing Module (SH_002)
```

---

## Known Limitations

1. **Network Issues:** No pattern for transient network failures (TODO: Add SH_011)
2. **Kaggle API Rate Limits:** No automatic backoff for 429 errors
3. **Interactive Commands:** Cannot handle commands requiring user input
4. **Stateful Sessions:** Does not persist state across session restarts

---

## Future Enhancements

- [ ] Add pattern for Kaggle API rate limiting (429)
- [ ] Integrate with MCP memory for cross-session learning
- [ ] Add ML-specific patterns (leakage detection, CV-LB gap alerts)
- [ ] Implement "healing confidence score" based on historical success rates

---

## References

- Original friction patterns: `/home/kizabgd/Desktop/kaggle-arena/friction_patterns.json`
- Healing report log: `logs/HEALING_REPORT.md` (in workspace)
- Related: Trinity Protocol `ORCHESTRATION_RULES.json`
