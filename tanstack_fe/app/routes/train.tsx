import { createFileRoute, useSearch } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { Button } from "../components/ui/button";
import { Loader2, Cog } from 'lucide-react';
import SelectList from '~/components/ui/selectList';
import { z } from 'zod';
import { baseUrl, chunkSizeOptions, chunkSizeTooltipText, fileTypeOptions } from '~/config';
import TooltipBase from '~/components/ui/toolTip';
import { useSettings } from '~/contexts/SettingsContext';
import { FileType } from '~/types';

const searchSchema = z.object({
  fileType: z.string().optional()
});

export const Route = createFileRoute('/train')({
  component: TrainModelComponent,
  validateSearch: searchSchema
})

function TrainModelComponent() {
    const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState<string[]>([]);
    const [status, setStatus] = useState('');
    const { chunkSize, setChunkSize, selectFileType, setSelectFileType } = useSettings();
  
    useEffect(() => {
        // Connect to WebSocket
        const socket = new WebSocket("ws://localhost:8000/api/train/ws");
    
        socket.onopen = () => {
          console.log("WebSocket connected");
        };
        
        socket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log('data ->', data)
          setStatus(data.message); // Update status from WebSocket

          // If detailed results exist, use the first result for status and map messages
          if (data.details && data.details.results && data.details.results.length > 0) {
            setMessages(data.details.results.map((res: any) => res.message));
          } else if (data.message) {
            setMessages([data.message]);
          }

          if (["completed", "error", "empty", "skipped"].includes(data.status)) {
            setLoading(false);
          }

          if (["empty", "running"].includes(data.status)) {
            setMessages([]);
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
          const response = await fetch(`${baseUrl}/api/train?file_type=${selectFileType}&chunk_size=${chunkSize}`, {
            method: "POST",
          });
    
          if (!response.ok) {
            throw new Error("Failed to train model");
          }
        } catch (error) {
          setStatus("Error starting training");
          console.error(error);
          setLoading(false);
        }
      };
    
      const handleFileTypeChange = (newFileType: FileType) => {
        setSelectFileType(newFileType);
        setChunkSize('');
        setMessages([]); 
        setStatus('')
      };

      const handleChunkSizeChange = (chunks: string) => {
        setChunkSize(chunks);
        setMessages([]); 
        setStatus('')
      }


    return (
        <div className="flex flex-col items-center justify-center h-screen space-y-6">
            <h3 className="text-center text-2xl font-semibold">
            Train the model
            </h3>
            <h5 className="text-center text-md font-italic">
            Choose a file to process and optionally set the chunk size
            </h5>
            <div className="flex flex-col items-center justify-between">
            <div className="flex items-center mb-4">
            <label className="text-gray-300 mr-2">
              File type <span className="text-red-500">*</span>
            </label>
              <SelectList
                options={fileTypeOptions}
                selectedValue={selectFileType}
                disabled={loading}
                onChange={handleFileTypeChange}
                placeholder="Select file type"
              />
            </div>
            <div className="flex items-center mb-4">
              <TooltipBase text={chunkSizeTooltipText} />
              <label className="text-gray-300 mr-2">Chunk size:</label>
              <SelectList
                options={chunkSizeOptions}
                selectedValue={chunkSize}
                disabled={loading}
                onChange={handleChunkSizeChange}
                placeholder="Select chunk size"
              />
            </div>

            <Button
              onClick={startTraining}
              disabled={loading}
              className="my-5 bg-primary hover:bg-primary/90"
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
