export type FileType = 'pdf' | 'csv';

export type ChartDataType = {
    labels: string[];
    values: number[];
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