import * as fs from 'node:fs';
const MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024; // 5MB
const MAX_ROTATED_FILES = 3;
/**
 * Rotates a log file if it exceeds MAX_LOG_SIZE_BYTES.
 * Keeps up to MAX_ROTATED_FILES rotated copies (e.g., debug.log.1, debug.log.2, debug.log.3).
 * The oldest rotation is deleted when the limit is exceeded.
 */
export function rotateLogIfNeeded(logPath) {
    try {
        if (!fs.existsSync(logPath))
            return;
        const stats = fs.statSync(logPath);
        if (stats.size < MAX_LOG_SIZE_BYTES)
            return;
        // Shift existing rotated files: .3 → deleted, .2 → .3, .1 → .2
        for (let i = MAX_ROTATED_FILES; i >= 1; i--) {
            const src = `${logPath}.${i}`;
            const dst = `${logPath}.${i + 1}`;
            if (fs.existsSync(src)) {
                if (i === MAX_ROTATED_FILES) {
                    fs.unlinkSync(src); // Delete oldest
                }
                else {
                    fs.renameSync(src, dst);
                }
            }
        }
        // Rotate current log to .1
        fs.renameSync(logPath, `${logPath}.1`);
    }
    catch {
        // Silently ignore rotation failures — logging must never crash the process.
    }
}
