#!/usr/bin/env python3
"""
Diagnosis Engine for Pickle Rick Self-Healer Skill

This module provides regex-based error diagnosis and automated recovery
playbook execution based on friction_patterns.json.

Usage:
    python diagnosis_engine.py --error "No module named 'pandas'"
    python diagnosis_engine.py --file logs/error.log --auto-heal
"""

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class FrictionPattern:
    """Represents a single friction pattern from the registry."""
    id: str
    name: str
    regex: str
    category: str
    root_cause: str
    playbook: list[dict[str, Any]]
    severity: str
    _compiled_regex: re.Pattern = field(default=None, repr=False)
    
    def __post_init__(self):
        self._compiled_regex = re.compile(self.regex, re.MULTILINE | re.DOTALL)
    
    def match(self, text: str) -> re.Match | None:
        """Check if the pattern matches the error text."""
        return self._compiled_regex.search(text)
    
    def format_playbook_command(self, command_template: str, match: re.Match) -> str:
        """Format a playbook command with regex capture groups."""
        result = command_template
        for i, group in enumerate(match.groups(), start=1):
            placeholder = f"{{{i-1}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(group))
        return result


@dataclass
class DiagnosisResult:
    """Result of error diagnosis."""
    matched: bool
    pattern: FrictionPattern | None = None
    match_object: re.Match | None = None
    confidence: float = 0.0
    suggested_actions: list[dict[str, Any]] = field(default_factory=list)
    root_cause: str = ""
    severity: str = "unknown"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "matched": self.matched,
            "pattern_id": self.pattern.id if self.pattern else None,
            "pattern_name": self.pattern.name if self.pattern else None,
            "category": self.pattern.category if self.pattern else None,
            "root_cause": self.root_cause,
            "severity": self.severity,
            "confidence": self.confidence,
            "suggested_actions": self.suggested_actions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class DiagnosisEngine:
    """
    Main diagnosis engine that matches errors against friction patterns
    and executes recovery playbooks.
    """
    
    def __init__(self, patterns_file: str | None = None):
        """
        Initialize the diagnosis engine.
        
        Args:
            patterns_file: Path to friction_patterns.json. If None, uses
                          the default location in the self-healer skill directory.
        """
        if patterns_file is None:
            # Default location relative to this script (../data/friction_patterns.json)
            # For scripts/ version, we look for it in the root or skills dir
            script_dir = Path(__file__).parent
            # Try root first
            patterns_file = script_dir.parent / "friction_patterns.json"
            if not patterns_file.exists():
                # Try skill dir
                patterns_file = script_dir.parent / "skills" / "self-healer" / "data" / "friction_patterns.json"
        
        self.patterns_file = Path(patterns_file)
        self.patterns: list[FrictionPattern] = []
        self.config: dict[str, Any] = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load friction patterns from JSON file."""
        if not self.patterns_file.exists():
            raise FileNotFoundError(f"Patterns file not found: {self.patterns_file}")
        
        with open(self.patterns_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.config = data.get("detection_logic", {})
        self.config["escalation_rules"] = data.get("escalation_rules", {})
        
        for pattern_data in data.get("patterns", []):
            pattern = FrictionPattern(
                id=pattern_data["id"],
                name=pattern_data["name"],
                regex=pattern_data["regex"],
                category=pattern_data["category"],
                root_cause=pattern_data["root_cause"],
                playbook=pattern_data["playbook"],
                severity=pattern_data["severity"]
            )
            self.patterns.append(pattern)
        
        print(f"[DiagnosisEngine] Loaded {len(self.patterns)} friction patterns", 
              file=sys.stderr)
    
    def diagnose(self, error_text: str) -> DiagnosisResult:
        """
        Diagnose an error by matching against all friction patterns.
        
        Args:
            error_text: The error message or traceback to analyze.
        
        Returns:
            DiagnosisResult with matched pattern and suggested actions.
        """
        # Try to match each pattern
        for pattern in self.patterns:
            match = pattern.match(error_text)
            if match:
                # Format root cause with capture groups
                root_cause = pattern.root_cause
                for i, group in enumerate(match.groups(), start=1):
                    root_cause = root_cause.replace(f"{{{i}}}", str(group))
                
                # Build suggested actions from playbook
                actions = []
                for step in pattern.playbook:
                    action = step.copy()
                    if action.get("action") == "shell" and "command" in action:
                        action["command"] = pattern.format_playbook_command(
                            action["command"], match
                        )
                    actions.append(action)
                
                return DiagnosisResult(
                    matched=True,
                    pattern=pattern,
                    match_object=match,
                    confidence=0.95,  # High confidence on regex match
                    suggested_actions=actions,
                    root_cause=root_cause,
                    severity=pattern.severity
                )
        
        # No match found - generic diagnosis
        return DiagnosisResult(
            matched=False,
            confidence=0.0,
            root_cause="Unknown error - no matching friction pattern",
            severity="unknown",
            suggested_actions=[
                {"action": "invoke_skill", "skill": "code-debugger", 
                 "context": f"Generic error: {error_text[:200]}"}
            ]
        )
    
    def execute_playbook(self, result: DiagnosisResult, 
                        working_dir: str | None = None,
                        dry_run: bool = False) -> dict[str, Any]:
        """
        Execute the recovery playbook for a diagnosed error.
        
        Args:
            result: DiagnosisResult from diagnose()
            working_dir: Working directory for shell commands
            dry_run: If True, log commands without executing
        
        Returns:
            Dictionary with execution results
        """
        if not result.matched:
            return {"success": False, "reason": "No matched pattern to execute"}
        
        working_dir = working_dir or os.getcwd()
        execution_log = []
        all_success = True
        
        print(f"\n[Self-Healer] Executing playbook for {result.pattern.name}", 
              file=sys.stderr)
        
        for i, action in enumerate(result.suggested_actions, start=1):
            action_type = action.get("action")
            step_result = {"step": i, "action": action_type, "success": True}
            
            try:
                if action_type == "shell":
                    command = action.get("command", "")
                    if dry_run:
                        print(f"  [DRY-RUN] Would execute: {command}", file=sys.stderr)
                        step_result["command"] = command
                    else:
                        print(f"  [EXEC] {command}", file=sys.stderr)
                        proc = subprocess.run(
                            command,
                            shell=True,
                            cwd=working_dir,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        step_result["returncode"] = proc.returncode
                        step_result["stdout"] = proc.stdout
                        step_result["stderr"] = proc.stderr
                        if proc.returncode != 0:
                            step_result["success"] = False
                            all_success = False
                
                elif action_type == "retry":
                    max_attempts = action.get("max_attempts", 3)
                    backoff = self.config.get("backoff_base_seconds", 2)
                    step_result["max_attempts"] = max_attempts
                    step_result["backoff_seconds"] = backoff
                    print(f"  [RETRY] Will retry up to {max_attempts} times "
                          f"with {backoff}s exponential backoff", file=sys.stderr)
                
                elif action_type == "adjust_timeout":
                    multiplier = action.get("multiplier", 1)
                    step_result["multiplier"] = multiplier
                    print(f"  [TIMEOUT] Adjusting timeout by {multiplier}x", 
                          file=sys.stderr)
                
                elif action_type == "log_warning":
                    message = action.get("message", "")
                    print(f"  [WARN] {message}", file=sys.stderr)
                    step_result["message"] = message
                
                elif action_type == "verify_env":
                    vars_to_check = action.get("vars", [])
                    missing = []
                    for var in vars_to_check:
                        if not os.environ.get(var):
                            missing.append(var)
                    step_result["missing_vars"] = missing
                    if missing:
                        print(f"  [ENV] Missing variables: {missing}", file=sys.stderr)
                        step_result["success"] = False
                        all_success = False
                
                elif action_type == "invoke_skill":
                    skill = action.get("skill", "code-debugger")
                    context = action.get("context", "")
                    print(f"  [SKILL] Invoking {skill}: {context}", file=sys.stderr)
                    step_result["skill"] = skill
                    step_result["context"] = context
                
                elif action_type == "file_edit":
                    # Placeholder for file edit operations
                    target = action.get("target", "")
                    operation = action.get("operation", "")
                    print(f"  [FILE] {operation} on {target}", file=sys.stderr)
                    step_result["target"] = target
                    step_result["operation"] = operation
            
            except subprocess.TimeoutExpired:
                step_result["success"] = False
                step_result["error"] = "Command timed out"
                all_success = False
            except Exception as e:
                step_result["success"] = False
                step_result["error"] = str(e)
                all_success = False
            
            execution_log.append(step_result)
        
        return {
            "success": all_success,
            "pattern_id": result.pattern.id,
            "pattern_name": result.pattern.name,
            "execution_log": execution_log,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def log_healing_attempt(self, error_text: str, result: DiagnosisResult,
                           execution_result: dict, log_file: str | None = None):
        """
        Log a healing attempt to the healing report.
        
        Args:
            error_text: Original error message
            result: DiagnosisResult
            execution_result: Result from execute_playbook()
            log_file: Path to log file (default: logs/HEALING_REPORT.md)
        """
        if log_file is None:
            log_file = "logs/HEALING_REPORT.md"
        
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"""
## Healing Attempt - {timestamp}

**Pattern Matched:** {result.pattern.name if result.pattern else 'None'}  
**Pattern ID:** {result.pattern.id if result.pattern else 'N/A'}  
**Severity:** {result.severity}  
**Category:** {result.pattern.category if result.pattern else 'N/A'}

### Error Text
```
{error_text[:1000]}
```

### Root Cause
{result.root_cause}

### Execution Result
- Success: {execution_result.get('success', False)}
- Steps Executed: {len(execution_result.get('execution_log', []))}

### Recovery Actions Taken
"""
        for step in execution_result.get("execution_log", []):
            status = "✓" if step.get("success") else "✗"
            entry += f"- [{status}] Step {step['step']}: {step['action']}\n"
        
        entry += "\n---\n"
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        
        print(f"[Self-Healer] Logged to {log_path}", file=sys.stderr)


def main():
    """CLI entry point for diagnosis engine."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Pickle Rick Self-Healer Diagnosis Engine"
    )
    parser.add_argument(
        "--error", "-e",
        help="Error message to diagnose"
    )
    parser.add_argument(
        "--file", "-f",
        help="File containing error message/traceback"
    )
    parser.add_argument(
        "--auto-heal",
        action="store_true",
        help="Automatically execute recovery playbook"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without executing"
    )
    parser.add_argument(
        "--patterns",
        help="Custom path to friction_patterns.json"
    )
    parser.add_argument(
        "--working-dir", "-d",
        help="Working directory for shell commands"
    )
    
    args = parser.parse_args()
    
    # Get error text
    error_text = ""
    if args.error:
        error_text = args.error
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            error_text = f.read()
    else:
        # Read from stdin
        error_text = sys.stdin.read()
    
    if not error_text.strip():
        print("Error: No error text provided", file=sys.stderr)
        sys.exit(1)
    
    # Initialize engine and diagnose
    engine = DiagnosisEngine(patterns_file=args.patterns)
    result = engine.diagnose(error_text)
    
    # Output diagnosis
    print("\n" + "="*60)
    print("DIAGNOSIS RESULT")
    print("="*60)
    
    if result.matched:
        print(f"✓ Pattern Matched: {result.pattern.name} ({result.pattern.id})")
        print(f"  Category: {result.pattern.category}")
        print(f"  Severity: {result.severity}")
        print(f"  Root Cause: {result.root_cause}")
        print(f"\n  Suggested Actions ({len(result.suggested_actions)}):")
        for i, action in enumerate(result.suggested_actions, start=1):
            action_type = action.get("action")
            if action_type == "shell":
                print(f"    {i}. [SHELL] {action.get('command')}")
            else:
                print(f"    {i}. [{action_type.upper()}] {action}")
    else:
        print("✗ No matching friction pattern found")
        print(f"  Root Cause: {result.root_cause}")
        print("  Suggestion: Invoke code-debugger skill for manual diagnosis")
    
    print("="*60 + "\n")
    
    # Auto-heal if requested
    if args.auto_heal and result.matched:
        print("Executing recovery playbook...\n")
        execution_result = engine.execute_playbook(
            result,
            working_dir=args.working_dir,
            dry_run=args.dry_run
        )
        
        print("\n" + "="*60)
        print("EXECUTION RESULT")
        print("="*60)
        print(f"Success: {execution_result['success']}")
        print(f"Pattern: {execution_result['pattern_name']}")
        
        for step in execution_result.get("execution_log", []):
            status = "✓" if step.get("success") else "✗"
            print(f"  [{status}] Step {step['step']}: {step['action']}")
        
        print("="*60 + "\n")
        
        # Log the attempt
        engine.log_healing_attempt(error_text, result, execution_result)
        
        sys.exit(0 if execution_result["success"] else 1)
    
    # Output JSON for programmatic use
    print("\nJSON Output:")
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
