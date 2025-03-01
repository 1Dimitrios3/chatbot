import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";

export function PdfList() {
  const queryClient = useQueryClient();

  const { data: pdfs = [], isLoading, error } = useQuery({
    queryKey: ["pdfs"],
    queryFn: async () => {
      const res = await fetch("http://localhost:8000/api/pdf/list");
      if (!res.ok) throw new Error("Failed to fetch PDFs");
      const data = await res.json();
      return Array.isArray(data) ? data : data.pdfs;
    },
  });

  const deleteMutation = useMutation(
    {
      mutationFn: async (filename: string) => {
        const res = await fetch(
          `http://localhost:8000/api/pdf/delete?filename=${encodeURIComponent(
            filename
          )}`,
          { method: "DELETE" }
        );
        if (!res.ok) throw new Error("Failed to delete PDF");
        return res.json();
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["pdfs"] });
      },
    },
    queryClient
  );

  if (isLoading) {
    return <p className="text-center text-gray-500">Loading PDFs...</p>;
  }

  if (error) {
    console.error('error ->', error);
    return <p className="text-center text-red-500">Error loading PDFs.</p>;
  }

  return (
    <div className="max-w-md mx-auto mt-8 space-y-2">
    {pdfs?.length === 0 ? (
      <p className="text-center text-gray-500">No PDFs available.</p>
    ) : (
        pdfs?.map((pdf: string) => (
        <div
          key={pdf}
          className="flex items-center justify-between p-2 border border-gray-500 rounded-lg"
        >
          <span className="text-gray-500 text-sm truncate">{pdf}</span>
          <button
            onClick={() => deleteMutation.mutate(pdf)}
            className="text-gray-500 hover:text-red-500 focus:outline-none"
            aria-label={`Delete ${pdf}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))
    )}
  </div>
  );
}
