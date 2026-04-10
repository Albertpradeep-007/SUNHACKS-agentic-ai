import axios from 'axios';
import { BaseChatModel } from '@langchain/core/language_models/chat_models';

/**
 * Service to orchestrate requests to the local Ollama LLM API.
 * Ensures data stays private and leverages fast local inferences.
 */
export class OllamaService {
    private baseUrl: string;
    private model: string;

    constructor(model: string = 'llama3', baseUrl: string = 'http://localhost:11434/api') {
        this.model = model;
        this.baseUrl = baseUrl;
    }

    /**
     * Test connection to the local Ollama instance
     * Call this on backend startup to ensure the agent core is ready.
     */
    public async verifyConnection(): Promise<boolean> {
        try {
            // Root endpoint of Ollama usually serves a 200 OK "Ollama is running"
            const response = await axios.get(`http://localhost:11434/`);
            if (response.status === 200) {
                console.log('✅ System Online: Successfully connected to local Ollama instance.');
                return true;
            }
            return false;
        } catch (error: any) {
            console.error('❌ Connection Failed: Could not connect to Ollama. Ensure it is running.', error.message);
            return false;
        }
    }

    /**
     * Generate completion with Ollama API using streaming enabled
     */
    public async generateStream(prompt: string, onToken: (token: string) => void): Promise<string> {
        try {
            const response = await axios.post(`${this.baseUrl}/generate`, {
                model: this.model,
                prompt: prompt,
                stream: true
            }, {
                responseType: 'stream'
            });

            return new Promise((resolve, reject) => {
                let fullResponse = '';
                response.data.on('data', (chunk: Buffer) => {
                    const lines = chunk.toString().split('\n').filter(line => line.trim() !== '');
                    for (const line of lines) {
                        const parsed = JSON.parse(line);
                        const token = parsed.response;
                        fullResponse += token;
                        onToken(token); // Real-time emit to frontend/terminal
                    }
                });

                response.data.on('end', () => resolve(fullResponse));
                response.data.on('error', (err: any) => reject(err));
            });
        } catch (error: any) {
            console.error('[OllamaService] Error generating response:', error.message);
            throw error;
        }
    }
}

// ==========================================
// Quick Verification Script (Run via ts-node)
// ==========================================
if (require.main === module) {
    (async () => {
        const ollama = new OllamaService('llama3');
        const isConnected = await ollama.verifyConnection();
        
        if (isConnected) {
            console.log("\n[Agent]: Testing real-time stream...");
            await ollama.generateStream(
                "Write a short haiku about modular local AI systems.", 
                (chunk) => process.stdout.write(chunk)
            );
            console.log("\n");
        }
    })();
}
