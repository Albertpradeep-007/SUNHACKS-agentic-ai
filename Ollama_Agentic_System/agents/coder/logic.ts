import { OllamaService } from '../../backend/src/services/OllamaService';
import { tools } from './tools';
import { SYSTEM_PROMPT } from './prompt';

export class CoderAgent {
    private llm: OllamaService;
    private maxIterations = 10; // Prevent infinite loops

    constructor() {
        // Automatically mapped to your RTX 3050 VRAM profile
        this.llm = new OllamaService('llama3'); 
    }

    public async run(task: string): Promise<string> {
        let history = `${SYSTEM_PROMPT}\n\nUser Task: ${task}\n`;
        let iteration = 0;

        console.log(`\n[CoderAgent] Starting Mission: "${task}"`);

        while (iteration < this.maxIterations) {
            iteration++;
            console.log(`\n\x1b[36m--- Agent Loop ${iteration}/${this.maxIterations} ---\x1b[0m`);
            
            // Wait for the LLM to process history and give us a stream
            // We strip 'Observation' chunks from history occasionally, but for a 8k context size, 10 loop iterations fit perfectly.
            const response = await this.llm.generateStream(history, (token) => {
                // Live terminal typing effect
                process.stdout.write(token);
            });

            // Append what the LLM decided to our running context
            history += response + '\n';

            // Check if the agent decided it's done
            if (response.includes("Final Answer:")) {
                const finalAnswer = response.split("Final Answer:")[1].trim();
                console.log(`\n\n\x1b[32m[CoderAgent] Mission Accomplished!\x1b[0m`);
                return finalAnswer;
            }

            // Extract the Action JSON using Regex
            const actionRegex = /Action:\s*({.*})/is;
            const match = response.match(actionRegex);

            if (match) {
                try {
                    const actionJson = JSON.parse(match[1]);
                    const toolName = actionJson.tool as keyof typeof tools;
                    const toolArgs = actionJson.args;

                    if (tools[toolName]) {
                        console.log(`\n\x1b[33m[System] Executing Tool: ${toolName}\x1b[0m`);
                        
                        // Execute tool logic dynamically
                        // @ts-ignore
                        const result = await tools[toolName](toolArgs);
                        
                        // Feed result back to the LLM context memory
                        const observation = `Observation: ${result}\n`;
                        console.log(`\x1b[35m[System] Tool completed. Feeding Observation back to LLM... (${result.length} chars)\x1b[0m`);
                        history += observation;
                    } else {
                        history += `Observation: Execution Error - Tool '${toolName}' not found.\n`;
                    }
                } catch (e: any) {
                    history += `Observation: Parsing Error - Invalid JSON in Action. ${e.message}\n`;
                }
            } else {
                history += `Observation: format error - No valid 'Action:' or 'Final Answer:' found. Try again using the strict format.\n`;
            }
        }

        return "Error: Agent reached maximum iterations without reaching a Final Answer. Increase Max Loops.";
    }
}

// ==========================================
// TEST SCRIPT (Run via ts-node / tsx)
// ==========================================
if (require.main === module) {
    (async () => {
        const agent = new CoderAgent();
        const testMission = "Create a new file called 'hello_rtx3050.txt' in the current directory and write 'Agentic Architecture activated by LLaMa3 entirely on 6GB VRAM!' inside it. Then read the file back to verify, and summarize the output.";
        await agent.run(testMission);
    })();
}
