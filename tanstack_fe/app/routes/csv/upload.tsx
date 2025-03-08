import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { createServerFn } from '@tanstack/start';
import { useState, useRef } from 'react';
import { Button } from "../../components/ui/button";
import { FileText } from "lucide-react";
import { CsvList } from '~/components/ui/CsvList';
import { z } from 'zod';
import { useQueryClient } from '@tanstack/react-query';

const searchSchema = z.object({
  fileType: z.string().optional()
});

export const Route = createFileRoute('/csv/upload')({
  component: UploadCsvComponent,
  validateSearch: searchSchema,
});

const uploadFile = createServerFn({ method: 'POST' })
  .validator((formData: FormData) => {
    if (!(formData instanceof FormData)) {
      throw new Error('Invalid form data');
    }
    return formData;
  })
  .handler(async ({ data }) => {
    const response = await fetch("http://localhost:8000/api/csv/upload", {
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

function UploadCsvComponent() {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);
    const [uploaded, setUploaded] = useState(false);
    const [message, setMessage] = useState("");
    const queryClient = useQueryClient();
    const navigate = useNavigate();

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
          queryClient.invalidateQueries({ queryKey: ["csvs"] });
          setUploaded(true);

          navigate({
            from: '/csv/upload',
            search: (prev) => ({ ...prev, fileType: "csv" }),
          });
          
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
                Upload your CSV
            </h3>
            <h5 className="text-center text-sm font-italic">
                Must be a .csv file. Max allowed files: 1
            </h5>
            <div className="flex flex-col items-center justify-center space-y-4">
                {uploaded && (
                    <FileText className="w-12 h-12 text-gray-400" /> 
                )}
                {/* Hidden file input */}
                <input
                    type="file"
                    accept=".csv"
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
                    {uploading ? "Uploading..." : "Upload CSV"}
                </Button>
                {message && <p className="text-sm text-gray-600">{message}</p>}
            </div>
            <CsvList />
        </div>
    );
}
