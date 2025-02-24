import { streamAsyncIterator } from "./asyncIterator";

interface StreamChatParams {
  sessionId: string;
  message: string;
  selectModel: string;
  onChunk: (chunk: string) => void;
}

async function streamChat({ sessionId, message, selectModel, onChunk }: StreamChatParams) {
  const response = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, model: selectModel }),
  });
  if (!response.body) {
    throw new Error("No streaming body in response");
  }
  const reader = response.body.getReader();
  let fullResponse = "";
  for await (const chunk of streamAsyncIterator(reader)) {
    fullResponse += chunk;
    onChunk(fullResponse);
  }
  return fullResponse;
}

export { streamChat };