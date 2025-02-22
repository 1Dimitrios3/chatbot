import { createFileRoute } from '@tanstack/react-router';
import { createServerFn } from '@tanstack/start';
import { useEffect, useState } from 'react';
import { Button } from "../components/ui/button";
import { Loader2, Cog } from 'lucide-react';

export const Route = createFileRoute('/train')({
  // component: TrainModelComponent,
  component: () => {
    // add auth check
    // if (localStorage.getItem('train') !== 'true') {
      if (false) {
      return null;
    }

    return <TrainModelComponent />
  }
})

function TrainModelComponent() {
    const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState<string[]>([]);
    console.log('messages', messages)
    const [status, setStatus] = useState('');

    useEffect(() => {
        // Connect to WebSocket
        const socket = new WebSocket("ws://localhost:8000/api/train/ws");
    
        socket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setStatus(data.message); // Update status from WebSocket

                // If detailed results are available, extract messages
        if (data.details && data.details.results) {
            const newMessages = data.details.results.map((res: any) => res.message);
            setMessages(newMessages);
        }

          if (data.status === "completed" || data.status === "error" || data.status === "empty") {
            setLoading(false);
          }
        };
    
        socket.onerror = () => {
          console.error("WebSocket error");
        };
    
        socket.onclose = () => {
          console.log("WebSocket disconnected");
        };
    
        return () => {
          socket.close(); // Clean up WebSocket connection on unmount
        };
      }, []);
    
      const startTraining = async () => {
        setLoading(true);
        setStatus("Starting training...");
        setMessages([]);
    
        try {
          const response = await fetch("http://localhost:8000/api/train", {
            method: "POST",
          });
    
          if (!response.ok) {
            throw new Error("Failed to train model");
          }
    
          const result = await response.json();
          setStatus(result.message);
        } catch (error) {
          setStatus("Error starting training");
          console.error(error);
          setLoading(false);
        }
      };
    


    return (
        <div className="flex flex-col items-center justify-center h-screen space-y-6">
            <h3 className="text-center text-2xl font-semibold">
            Train the model
            </h3>
            <h5 className="text-center text-sm font-italic">
            Wait for the process to finish
            </h5>
            <div className="flex flex-col items-center justify-center space-y-4">
   
            <Button
              onClick={startTraining}
              disabled={loading}
              className="bg-primary hover:bg-primary/90"
              variant="default"
              size="lg"
            > 
              {loading ? (
                <><span>Training...</span><Loader2 className="h-4 w-4 animate-spin" /></>
              ) : (
                <><span>Train</span><Cog className="h-4 w-4" /></>
              )}
              <span className="sr-only">Send message</span>
            </Button>

        {status && <p className="text-sm text-gray-600">{status}</p>}
        <hr />
        {messages.length > 0 && (
          <div className="mt-4 p-3 border border-gray-700 rounded-md w-80 text-sm text-gray-300 bg-gray-800">
            <strong>Training Details:</strong>
            <ul className="list-disc ml-4">
              {messages.map((msg, index) => (
                <li key={index}>{msg}</li>
              ))}
            </ul>
          </div>
        )}
        </div>
      </div>
      )
}
