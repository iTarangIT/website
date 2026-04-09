import Groq from "groq-sdk";

let groqClient: Groq | null = null;

export function getGroqClient(): Groq {
  if (groqClient) return groqClient;

  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    throw new Error("[Groq] Missing GROQ_API_KEY in .env.local");
  }

  groqClient = new Groq({ apiKey });
  return groqClient;
}

/**
 * Call Groq chat completions with a system prompt + user message.
 * Returns the full text response (non-streaming).
 */
export async function generateAnswer(
  systemPrompt: string,
  userMessage: string
): Promise<string> {
  const client = getGroqClient();
  const model = process.env.GROQ_MODEL || "llama-3.3-70b-versatile";

  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userMessage },
    ],
    temperature: 0.15,
    max_tokens: 1500,
  });

  return response.choices[0]?.message?.content ?? "";
}

/**
 * Stream a Groq response (for real-time chat UI).
 */
export async function generateAnswerStream(
  systemPrompt: string,
  userMessage: string
) {
  const client = getGroqClient();
  const model = process.env.GROQ_MODEL || "llama-3.3-70b-versatile";

  return client.chat.completions.create({
    model,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userMessage },
    ],
    temperature: 0.15,
    max_tokens: 1500,
    stream: true,
  });
}
