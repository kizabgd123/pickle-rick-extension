import { execSync, spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const LOG_FILE = 'deployment_log.md';
const BASELINE_FILE = 'baseline.json';
const EXTENSION_DIR = 'extension';
const RETRY_LIMIT = 2;

function log(message, type = 'INFO') {
    const timestamp = new Date().toISOString();
    const formattedMessage = `[${timestamp}] [${type}] ${message}`;
    console.log(formattedMessage);
    fs.appendFileSync(LOG_FILE, `${formattedMessage}\n`);
}

function runCommand(command, cwd = process.cwd()) {
    log(`Running: ${command} in ${cwd}`);
    try {
        const result = execSync(command, { cwd, encoding: 'utf-8', stdio: 'pipe' });
        return { success: true, output: result };
    } catch (error) {
        return { success: false, output: error.stdout || error.stderr || error.message };
    }
}

async function start() {
    log('--- Starting Self-Healing Deployment Pipeline ---', 'HEADER');

    // 1. Pre-deployment validation & baseline
    log('Step 1: Validation & Baseline metrics...');
    const testResult = runCommand('npm run test', EXTENSION_DIR);
    const coverageResult = runCommand('npm run test:coverage', EXTENSION_DIR);
    
    const baseline = {
        timestamp: new Date().toISOString(),
        testsPassed: testResult.success,
        coverage: coverageResult.success ? 'Captured' : 'Failed'
    };
    fs.writeFileSync(BASELINE_FILE, JSON.stringify(baseline, null, 2));
    
    if (!testResult.success) {
        log('Pre-deployment tests failed. Aborting production deployment.', 'ERROR');
        return;
    }

    // 2. Deployment
    log('Step 2: Executing Deployment (Build)...');
    const deployResult = runCommand('npm run build', EXTENSION_DIR);
    if (!deployResult.success) {
        log('Deployment failed. Starting diagnosis...', 'WARNING');
        await diagnoseAndFix(deployResult.output, 0);
        return;
    }

    // 3. Post-deployment health checks
    log('Step 3: Post-deployment health checks...');
    const healthCheck = runCommand('node bin/setup.js --help', EXTENSION_DIR);
    if (!healthCheck.success) {
        log('Health check failed. Starting diagnosis...', 'WARNING');
        await diagnoseAndFix(healthCheck.output, 0);
    } else {
        log('Deployment successful and healthy! 🥒', 'SUCCESS');
    }
}

async function diagnoseAndFix(output, attempt) {
    if (attempt >= RETRY_LIMIT) {
        log(`Failed to fix after ${attempt} attempts. Rolling back...`, 'CRITICAL');
        rollback();
        return;
    }

    log(`Diagnosing failure (Attempt ${attempt + 1})...`);
    
    // Simple diagnosis logic
    if (output.includes('ELINT') || output.includes('eslint')) {
        log('Detected linting errors. Attempting to fix with lint:fix...');
        runCommand('npm run lint:fix', EXTENSION_DIR);
    } else if (output.includes('MODULE_NOT_FOUND')) {
        log('Detected missing dependencies. Running npm install...');
        runCommand('npm install', EXTENSION_DIR);
    } else if (output.includes('TS')) {
        log('Detected TypeScript errors. Attempting to re-build...');
    }

    log('Retrying deployment...');
    const retryDeploy = runCommand('npm run build', EXTENSION_DIR);
    if (retryDeploy.success) {
        const retryHealth = runCommand('node bin/setup.js --help', EXTENSION_DIR);
        if (retryHealth.success) {
            log('Healed successfully after intervention! 🥒', 'SUCCESS');
            return;
        }
    }
    
    // Recurse if still failing
    await diagnoseAndFix(retryDeploy.output + (retryDeploy.success ? '' : ''), attempt + 1);
}

function rollback() {
    log('Executing Rollback (Git Reset)...');
    // First, try to discard uncommitted changes
    runCommand('git checkout .');
    runCommand('git clean -fd');
    
    // If we're on a bad commit, we might need to go back one
    // runCommand('git reset --hard HEAD^'); 
    
    log('Rollback complete. Attempting to build last stable version...');
    runCommand('npm run build', EXTENSION_DIR);
}

start().catch(err => {
    log(`Fatal Pipeline Error: ${err.message}`, 'CRITICAL');
    process.exit(1);
});
