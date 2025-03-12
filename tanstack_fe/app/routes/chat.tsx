import { createFileRoute } from '@tanstack/react-router'
import { useState } from "react";
import { Bot, Loader2, MessageSquare, Send, User2, Copy, CheckCircle, } from "lucide-react";
import { useSession } from '~/hooks/useSession';
import Markdown from "react-markdown";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { streamChat } from '~/utils/streamChat';
import SelectList from '~/components/ui/selectList';
import { fileTypeOptions, modelOptions } from '~/config';
import ToggleGroupBase from '~/components/ui/toggleGroup';
import { FileType } from '~/types';
import React from 'react';

type Message = {
  role: "user" | "assistant" | "tool" | "system";
  content: string;
};

type ConversationCard = {
    user: Message;
    assistant: Message;
};

export const Route = createFileRoute("/chat")({
  component: AIChat,
});

function AIChat() {
    const [conversations, setConversations] = useState<ConversationCard[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [selectModel, setSelectModel] = useState("gpt-4o-mini")
    const [selectFileType, setSelectFileType] = useState<FileType>("pdf");

    const sessionId = useSession();

    const chatContainerRef = React.useRef<HTMLDivElement | null>(null);

    React.useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [conversations]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        const userMessage = input.trim();
        if (!userMessage) return;
    
        setInput("");
        setLoading(true);
            // Create a new card with the user message and an empty assistant message
        const newCard: ConversationCard = {
            user: { role: "user", content: userMessage },
            assistant: { role: "assistant", content: "" },
        };

        // Add the new card to the history
        setConversations((prev) => [...prev, newCard]);
        
        try {
        await streamChat({
          sessionId: sessionId || '',
          message: userMessage,
          selectModel: selectModel,
          selectedFileType: selectFileType,
          onChunk: (partialResponse: string) => {
            setConversations((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              updated[lastIndex] = {
                ...updated[lastIndex],
                assistant: { role: "assistant", content: partialResponse },
              };
              return updated;
            });
          }
        });
        } catch (error) {
          console.error("Error streaming response:", error);
        } finally {
          setLoading(false);
        }
      }

  return (
    <div className="flex flex-col min-h-screen">
      <div className="w-full p-4 flex items-center justify-between">
        <div className="flex-1 flex justify-center">
          <ToggleGroupBase 
            items={fileTypeOptions} 
            value={selectFileType}
            onValueChange={(value) => setSelectFileType(value)}
          />
        </div>
        <SelectList 
          options={modelOptions} 
          selectedValue={selectModel} 
          onChange={setSelectModel} 
          placeholder="Select a model..." 
        />
      </div>
      <div 
        ref={chatContainerRef} 
        className="flex-1 p-4 container mx-auto max-w-4xl space-y-4 pb-32 overflow-y-auto scrollbar-hide"
        style={{ maxHeight: "calc(100vh - 150px)" }}
        >
      {conversations.map((card, index) => (
          <div key={index} className="space-y-2">
            <AIMessage message={card.user} />
            <AIMessage message={card.assistant} loading={loading} />
          </div>
        ))}
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-zinc-800 border-t border-gray-700">
        <form onSubmit={handleSubmit} className="container mx-auto max-w-4xl">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <MessageSquare className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                className="flex-1 bg-zinc-900 border-gray-700 text-gray-100 pl-10"
                value={input}
                disabled={loading}
                placeholder="Ask your local AI Assistant..."
                onChange={(e) => setInput(e.target.value)}
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="bg-primary hover:bg-primary/90"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              <span className="sr-only">Send message</span>
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

const AIMessage: React.FC<{ message: Message, loading?: boolean }> = ({ message, loading }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch((err) => console.error("Failed to copy text: ", err));
  };
  
  return (
    <div
      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[80%] rounded-lg p-4 ${message.role === "user"
          ? "bg-primary text-black"
          : "bg-zinc-700 text-gray-100"
          }`}
      >
        <div className="flex items-center gap-2 mb-2" style={{ justifyContent: "space-between" }}>
          <span className="text-sm font-medium" style={{ display: "flex", gap: 10 }}>
            {message.role === "user" ? (
              <User2 className="h-4 w-4" />
            ) : (
              loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />
            )}

            <span>{message.role === "user" ? "You" : "Assistant"}</span>
          </span>
          {message.role === "assistant" && (
            <div className="relative inline-block">
              <button 
                onClick={copyToClipboard} 
                className="text-gray-400 hover:text-white transition"
                aria-label="Copy to clipboard"
              >
                {copied ? <CheckCircle className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
              </button>
              {copied && (
                <span
                  className="absolute top-0 left-full ml-2 text-xs bg-black text-white px-2 py-1 rounded shadow animate-fadeOut"
                  onAnimationEnd={() => setCopied(false)}
                >
                  Copied!
                </span>
              )}
            </div>
          )}
        </div>

        {message.role === "assistant" && loading && (
          <div className="flex items-center gap-2 text-gray-400">
            <span className="text-sm">Thinking...</span>
          </div>
        )}

        <article className={`prose max-w-none ${message.role === "user" ? "prose-invert prose-p:text-black prose-headings:text-black prose-strong:text-black prose-li:text-black" : "prose-invert prose-p:text-gray-100 prose-headings:text-gray-100 prose-strong:text-gray-100 prose-li:text-gray-100"}`}>
          <Markdown>{message.content}</Markdown>
        </article>
      </div>
    </div>
  )
}

