import { Groq } from "groq-sdk";
import { getContextForQuery } from "@/data/company-knowledge";

const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY,
});

export async function POST(req: Request) {
    try {
        const { messages } = await req.json();

        // Get the latest user message
        const lastUserMessage = messages[messages.length - 1]?.content || "";

        // Retrieve context based on the query
        const context = getContextForQuery(lastUserMessage);

        const systemPrompt = `You are a helpful, professional, and friendly AI assistant for iTarang Technologies.
Your sole purpose is to help users understand iTarang's services, products, and processes.

Context about iTarang:
${context}

Rules:
1. Try to answer the user's question using the context above.
2. If you don't know the exact answer from the context, state politely that you don't have that specific information, but that the user can contact our team at founders@itarang.in or +91-8920828425.
3. Keep your answers concise, clear, and action-oriented. Don't invent or hallucinate information about pricing or policies not mentioned in the context.
4. Format using markdown when helpful (like bolding key terms).`;

        const chatResponse = await groq.chat.completions.create({
            messages: [
                { role: "system", content: systemPrompt },
                ...messages.map((m: any) => ({
                    role: m.role,
                    content: m.content,
                })),
            ],
            model: process.env.GROQ_MODEL || "llama-3.3-70b-versatile",
            temperature: 0.2,
            stream: true,
        });

        const stream = new ReadableStream({
            async start(controller) {
                for await (const chunk of chatResponse) {
                    const text = chunk.choices[0]?.delta?.content || "";
                    if (text) {
                        controller.enqueue(new TextEncoder().encode(text));
                    }
                }
                controller.close();
            },
        });

        return new Response(stream, {
            headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
            },
        });
    } catch (error: any) {
        console.error("Chat API Error:", error);
        return new Response(JSON.stringify({ error: error.message || "Failed to fetch response" }), {
            status: 500,
            headers: { "Content-Type": "application/json" }
        });
    }
}
