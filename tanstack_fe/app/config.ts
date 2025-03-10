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
  { label: "100 rows", value: "100" },
  { label: "300 rows", value: "300" },
  { label: "500 rows", value: "500" },
  { label: "700 rows", value: "700" },
  { label: "900 rows", value: "900" }
]

export { modelOptions, fileTypeOptions, chunkSizeOptions };