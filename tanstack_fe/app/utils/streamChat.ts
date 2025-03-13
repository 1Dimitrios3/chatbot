import { FileType } from "~/types";
import { streamAsyncIterator } from "./asyncIterator";
import { baseUrl } from "~/config";

interface StreamChatParams {
  sessionId: string;
  message: string;
  selectModel: string;
  selectedFileType: FileType;
  onChunk: (chunk: string) => void;
}

async function streamChat({ sessionId, message, selectModel, selectedFileType, onChunk }: StreamChatParams) {
    const response = await fetch(`${baseUrl}/api/${selectedFileType}/chat`, {
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