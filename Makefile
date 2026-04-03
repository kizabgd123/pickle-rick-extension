# Pickle Rick Extension - Core Makefile
# "Shut Up and Compute"

.PHONY: help test-encoder diagnose-test clean status sync-docs

PYTHON = python3
SKILLS_DIR = skills
SCRIPTS_DIR = scripts
JAR_DIR = jar

help:
	@echo "🥒 Pickle Rick Extension - Core Registry"
	@echo ""
	@echo "Available Commands:"
	@echo "  make test-encoder      Run HardenedTargetEncoder self-test"
	@echo "  make diagnose-test     Test DiagnosisEngine with a sample error"
	@echo "  make status            Show completion status of Pickle Core skills"
	@echo "  make clean             Remove __pycache__ and temporary artifacts"
	@echo "  make sync-docs         Synchronize QWEN.md with jar state"

test-encoder:
	@echo "🚀 Testing HardenedTargetEncoder..."
	@$(PYTHON) $(SKILLS_DIR)/ml-researcher/scripts/target_encoder.py --test

diagnose-test:
	@echo "🔍 Testing DiagnosisEngine..."
	@$(PYTHON) $(SCRIPTS_DIR)/diagnosis_engine.py --error "ModuleNotFoundError: No module named 'xgboost'" --dry-run

status:
	@echo "📊 Pickle Core v2.0 Skill Status:"
	@echo "--------------------------------"
	@echo -n "Self-Healer:   " && [ -f $(SKILLS_DIR)/self-healer/scripts/diagnosis_engine.py ] && echo "✅ DONE" || echo "❌ MISSING"
	@echo -n "ML-Researcher: " && [ -f $(SKILLS_DIR)/ml-researcher/scripts/target_encoder.py ] && echo "✅ DONE" || echo "❌ MISSING"
	@echo -n "Infra (Logs):  " && [ -d logs ] && echo "✅ DONE" || echo "❌ MISSING"
	@echo "--------------------------------"

clean:
	@echo "🧹 Cleaning up slop..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -rf catboost_info
	@echo "Done."

sync-docs:
	@echo "🔄 Syncing JAR documentation (QWEN.md)..."
	@# This is a placeholder for the automated sync script if implemented
	@echo "Manual sync required or use 'pickle-sync' tool."

# Ensure logs directory exists
init:
	@mkdir -p logs
