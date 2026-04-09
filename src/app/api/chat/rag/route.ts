import { v4 as uuidv4 } from "uuid";
import { searchRelevantChunks } from "@/lib/retrieval/search";
import { buildSystemPrompt, buildUserMessage } from "@/lib/retrieval/prompt";
import { sanitizeOutput, validateUserInput } from "@/lib/retrieval/safety";
import { generateAnswerStream } from "@/lib/groq/client";
import { insertChatLog } from "@/lib/supabase/client";

export async function POST(request: Request) {
  const startTime = Date.now();

  try {
    const body = await request.json();
    const { message, sessionId, userId } = body;

    // Validate input
    const validation = validateUserInput(message);
    if (!validation.valid) {
      return Response.json({ error: validation.error }, { status: 400 });
    }

    const currentSessionId = sessionId || uuidv4();

    // Step 1: Retrieve relevant chunks
    const chunks = await searchRelevantChunks(message, {
      visibility: ["public"],
    });

    // Step 2: Build grounded prompt
    const systemPrompt = buildSystemPrompt(chunks);
    const userMessage = buildUserMessage(message);

    // Step 3: Call Groq with streaming
    const stream = await generateAnswerStream(systemPrompt, userMessage);

    // Build sources list for logging
    const sources = chunks.map((c) => ({
      fileName: c.metadata.fileName,
      chunkIndex: c.metadata.chunkIndex,
      score: c.score,
    }));

    // Stream response to client
    let fullResponse = "";
    const readableStream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of stream) {
            const text = chunk.choices[0]?.delta?.content || "";
            if (text) {
              fullResponse += text;
              controller.enqueue(new TextEncoder().encode(text));
            }
          }

          // Safety check on final output
          const safety = sanitizeOutput(fullResponse);
          if (!safety.safe) {
            // If blocked, clear stream and send safe message
            controller.enqueue(
              new TextEncoder().encode(
                "\n\n[Response filtered for safety reasons]"
              )
            );
          }

          controller.close();

          // Log the interaction (fire-and-forget)
          insertChatLog({
            session_id: currentSessionId,
            user_id: userId,
            user_message: message,
            assistant_message: safety.safe ? fullResponse : safety.text,
            sources,
            latency_ms: Date.now() - startTime,
          }).catch(() => {});
        } catch (err) {
          controller.error(err);
        }
      },
    });

    return new Response(readableStream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "X-Session-Id": currentSessionId,
        "X-Sources": JSON.stringify(sources),
      },
    });
  } catch (error) {
    console.error("[RAG Chat]", error);
    return Response.json(
      {
        error: "Failed to process your request. Please try again.",
      },
      { status: 500 }
    );
  }
}
