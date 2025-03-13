import { createFileRoute } from '@tanstack/react-router';
import { createServerFn } from '@tanstack/start';
import { useState, useRef, useMemo } from 'react';
import { Button } from "../../components/ui/button";
import { FileText } from "lucide-react"
import { PdfList } from '~/components/ui/PdfList';
import { useQueryClient } from '@tanstack/react-query';
import { baseUrl } from '~/config';

export const Route = createFileRoute('/pdf/upload')({
  component: UploadPdfComponent,
})

const uploadFile = createServerFn({ method: 'POST' })
  .validator((formData: FormData) => {
    if (!(formData instanceof FormData)) {
      throw new Error('Invalid form data');
    }
    return formData;
  })
  .handler(async ({ data }) => {
    const response = await fetch(`${baseUrl}/api/pdf/upload`, {
      method: "POST",
      body: data,
    });

    if (!response.ok) {
      const errorResponse = await response.json();
      throw new Error(errorResponse.detail || 'Failed to upload file');
    }

    const result = await response.json();
    return result;
});

function UploadPdfComponent() {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);
    const [uploaded, setUploaded] = useState(false);
    const [message, setMessage] = useState("");
    const queryClient = useQueryClient();

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
          queryClient.invalidateQueries({ queryKey: ["pdfs"] });
          setUploaded(true);
        } catch (error: any) {
          setMessage(error.message || "Upload failed. Please try again.");
        } finally {
          setUploading(false);
          event.target.value = "";
        }
      };

    return (
        <div className="flex flex-col items-center justify-center h-screen space-y-6">
            <h3 className="text-center text-2xl font-semibold">
            Upload your PDF
            </h3>
            <h5 className="text-center text-sm font-italic">
            Must be a .pdf file. Max allowed files: 5
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
        <PdfList />
      </div>
      )
}
