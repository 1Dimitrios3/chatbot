export type FileType = 'pdf' | 'csv';

export type PieChartData = {
  labels: string[];
  values: number[];
};

export type BarChartDataset = {
  label: string;
  data: number[];
  backgroundColor: string;
};

export type BarChartData = {
  labels: string[];
  datasets: BarChartDataset[];
};

export type ChartDataType = {
  pie_chart?: PieChartData;
  bar_chart?: BarChartData;
};

export type Message = {
  role: "user" | "assistant" | "tool" | "system";
  content: string;
  chartData?: ChartDataType;
};

export type ConversationCard = {
  user: Message;
  assistant: Message;
};