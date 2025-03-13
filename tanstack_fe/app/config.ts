const modelOptions = [
    { label: "GPT-4o-mini", value: "gpt-4o-mini" },
    { label: "GPT-4", value: "gpt-4" },
    { label: "GPT-4o", value: "gpt-4o" },
    { label: "GPT-3.5 Turbo", value: "gpt-3.5-turbo" }
  ];

const fileTypeOptions = [
    { label: "PDF", value: "pdf" },
    { label: "CSV", value: "csv" },
  ];

const chunkSizeOptions = [
  { label: "Select chunk size", value: "0" },
  { label: "50 segments", value: "50" },
  { label: "100 segments", value: "100" },
  { label: "200 segments", value: "200" },
  { label: "300 segments", value: "300" },
  { label: "500 segments", value: "500" },
  { label: "700 segments", value: "700" },
  { label: "900 segments", value: "900" }
]

const chunkSizeTooltipText = "For CSVs a segment is usually a row, for PDFs a paragraph or sentence group. Larger segments reduce API calls and speed up processing but use more memory and may hit rate limits. Smaller segments use less memory and allow better streaming but require more API calls.";

const baseUrl = 'http://localhost:8000';

export { 
  modelOptions, 
  fileTypeOptions, 
  chunkSizeOptions,
  chunkSizeTooltipText,
  baseUrl 
};