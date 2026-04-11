import { v4 as uuidv4 } from "uuid";
import { searchRelevantChunks } from "@/lib/retrieval/search";
import { buildSystemPrompt, buildUserMessage } from "@/lib/retrieval/prompt";
import { sanitizeOutput, validateUserInput } from "@/lib/retrieval/safety";
import { extractLead } from "@/lib/retrieval/leadCapture";
import { generateAnswerStream } from "@/lib/groq/client";
import { insertChatLog, insertLead } from "@/lib/supabase/client";
import type { Visibility } from "@/lib/embeddings/types";

export const maxDuration = 60;

export async function POST(request: Request) {
  const startTime = Date.now();

  try {
    const body = await request.json();
    const { message, sessionId, userId, userRole } = body as {
      message: string;
      sessionId?: string;
      userId?: string;
      userRole?: Visibility;
    };

    // Validate input
    const validation = validateUserInput(message);
    if (!validation.valid) {
      return Response.json({ error: validation.error }, { status: 400 });
    }

    const currentSessionId = sessionId || uuidv4();
    const role: Visibility = userRole ?? "public";

    // Step 1: Retrieve relevant chunks filtered by role
    const chunks = await searchRelevantChunks(message, { userRole: role });

    // If no chunks found, return a safe fallback
    if (chunks.length === 0) {
      const fallback =
        "I don't have enough information to answer that question. Please contact iTarang at founders@itarang.in or +91-8920828425.";

      insertChatLog({
        session_id: currentSessionId,
        user_id: userId,
        user_role: role,
        user_message: message,
        assistant_message: fallback,
        retrieved_sources_json: [],
        latency_ms: Date.now() - startTime,
      }).catch(() => {});

      return new Response(fallback, {
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "X-Session-Id": currentSessionId,
          "X-Sources": "[]",
        },
      });
    }

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

          // Extract lead data and strip marker from response
          const { cleanedResponse, lead } = extractLead(fullResponse);

          // Safety check on final output
          const safety = sanitizeOutput(cleanedResponse);
          if (!safety.safe) {
            controller.enqueue(
              new TextEncoder().encode(
                "\n\n[Response filtered for safety reasons]"
              )
            );
          }

          controller.close();

          // Save lead if captured (fire-and-forget)
          if (lead) {
            insertLead({
              session_id: currentSessionId,
              name: lead.name,
              phone: lead.phone,
              interest: message,
              source_message: cleanedResponse,
            }).catch(() => {});
          }

          // Log the interaction (fire-and-forget)
          insertChatLog({
            session_id: currentSessionId,
            user_id: userId,
            user_role: role,
            user_message: message,
            assistant_message: safety.safe ? cleanedResponse : safety.text,
            retrieved_sources_json: sources,
            latency_ms: Date.now() - startTime,
            blocked_reason: safety.safe ? undefined : safety.blocked,
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
