import * as fs from 'fs/promises';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export const tools = {
    /**
     * Reads a file from the local filesystem
     */
    readFileSync: async ({ path }: { path: string }) => {
        try {
            const data = await fs.readFile(path, 'utf8');
            return data;
        } catch (e: any) {
            return `Error reading file: ${e.message}`;
        }
    },
    
    /**
     * Writes text content to a local file
     */
    writeFileSync: async ({ path, content }: { path: string, content: string }) => {
        try {
            await fs.writeFile(path, content, 'utf8');
            return `Success: File written to ${path}`;
        } catch (e: any) {
            return `Error writing file: ${e.message}`;
        }
    },
    
    /**
     * Executes arbitrary shell commands on your Windows machine
     */
    executeShell: async ({ command }: { command: string }) => {
        try {
            // Using a timeout so rogue commands don't lock the agent forever
            const { stdout, stderr } = await execAsync(command, { timeout: 15000 });
            return `STDOUT:\n${stdout}\nSTDERR:\n${stderr}`;
        } catch (e: any) {
            return `Execution Failed: ${e.message}\nSTDOUT: ${e.stdout}\nSTDERR: ${e.stderr}`;
        }
    }
};

export const toolDescriptions = `
Available Tools (Use ONLY these):
1. run_command - executes a terminal script. Args: {"tool": "executeShell", "args": {"command": "string"}}
2. view_file - reads file content. Args: {"tool": "readFileSync", "args": {"path": "string"}}
3. write_to_file - writes new file content. Args: {"tool": "writeFileSync", "args": {"path": "string", "content": "string"}}
`;
