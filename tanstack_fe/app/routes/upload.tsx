import { createFileRoute } from '@tanstack/react-router';
import { createServerFn } from '@tanstack/start';
import { useState, useRef } from 'react';
import { Button } from "../components/ui/button";
import { FileText } from "lucide-react"

export const Route = createFileRoute('/upload')({
  component: UploadComponent,
})

const uploadFile = createServerFn({ method: 'POST' })
  .validator((formData: FormData) => {
    if (!(formData instanceof FormData)) {
      throw new Error('Invalid form data');
    }
    return formData;
  })
  .handler(async ({ data }) => {
    const response = await fetch("http://localhost:8000/api/upload", {
      method: "POST",
      body: data,
    });

    if (!response.ok) {
      throw new Error('Failed to upload file');
    }

    const result = await response.json();
    return result;
});

function UploadComponent() {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);
    const [uploaded, setUploaded] = useState(false);
    const [message, setMessage] = useState("");

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;
    
        setUploading(true);
        setMessage("");
    
        const formData = new FormData();
        formData.append("file", file);
    
        try {
          const data = await uploadFile({ data: formData });
          setMessage(data.message || "Upload successful!");
          setUploaded(true);
        } catch (error) {
          setMessage("Upload failed. Please try again.");
        } finally {
          setUploading(false);
          event.target.value = "";
        }
      };

    return (
        <div className="flex flex-col items-center justify-center h-screen space-y-6">
            <h3 className="text-center text-2xl font-semibold">
            Upload your dataset
            </h3>
            <h5 className="text-center text-sm font-italic">
            Must be a .pdf file
            </h5>
            <div className="flex flex-col items-center justify-center space-y-4">
            {uploaded && (
            <FileText className="w-12 h-12 text-gray-400" /> 
        )}
        {/* Hidden file input */}
        <input
            type="file"
            accept="application/pdf"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileChange}
        />
        <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            variant="default"
            size="lg"
        >
            {uploading ? "Uploading..." : "Upload PDF"}
        </Button>

        {message && <p className="text-sm text-gray-600">{message}</p>}
        </div>
      </div>
      )
}
