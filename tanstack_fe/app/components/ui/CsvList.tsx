import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { baseUrl } from "~/config";

export function CsvList() {
  const queryClient = useQueryClient();

  const { data: csvs = [], isLoading, error } = useQuery({
    queryKey: ["csvs"],
    queryFn: async () => {
      const res = await fetch(`${baseUrl}/api/csv/list`);
      if (!res.ok) throw new Error("Failed to fetch CSVs");
      const data = await res.json();
      return Array.isArray(data) ? data : data.csvs;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (filename: string) => {
      const res = await fetch(
        `${baseUrl}/api/csv/delete?filename=${encodeURIComponent(filename)}`,
        { method: "DELETE" }
      );
      if (!res.ok) throw new Error("Failed to delete CSV");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["csvs"] });
    },
  });

  if (isLoading) {
    return <p className="text-center text-gray-500">Loading CSVs...</p>;
  }

  if (error) {
    console.error("error ->", error);
    return <p className="text-center text-red-500">Error loading CSVs.</p>;
  }

  return (
    <div className="max-w-md mx-auto mt-8 space-y-2">
      {csvs?.length === 0 ? (
        <p className="text-center text-gray-500">No CSVs available.</p>
      ) : (
        csvs.map((csv: string) => (
          <div
            key={csv}
            className="flex items-center justify-between p-2 border border-gray-500 rounded-lg"
          >
            <span className="text-gray-500 text-sm truncate">{csv}</span>
            <button
              onClick={() => deleteMutation.mutate(csv)}
              className="text-gray-500 hover:text-red-500 focus:outline-none"
              aria-label={`Delete ${csv}`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))
      )}
    </div>
  );
}
