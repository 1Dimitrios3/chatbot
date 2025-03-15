import { baseUrl } from '~/config';
import { ConversationCard } from '~/types';
import { shouldShowPieChart, shouldShowBarChart } from '~/utils/regex';

async function fetchChartData(
  userMessage: string,
  sessionId: string,
  setConversations: React.Dispatch<React.SetStateAction<ConversationCard[]>>
) {
  // If the user's message doesn't indicate a chart request, skip fetching.
  if (!shouldShowPieChart(userMessage) && !shouldShowBarChart(userMessage)) {
    return;
  }
  
  console.log("Storing chart data for session:", sessionId);
  try {
    const response = await fetch(`${baseUrl}/api/csv/chart-data/${sessionId}`);
    if (response.ok) {
      const chartData = await response.json();
      // Update the last conversation card with the complete chartData object.
      setConversations((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        updated[lastIndex] = {
          ...updated[lastIndex],
          assistant: {
            ...updated[lastIndex].assistant,
            chartData: chartData,
          },
        };
        return updated;
      });
    } else {
      console.error("Chart data not found for session:", sessionId);
    }
  } catch (error) {
    console.error("Error fetching chart data:", error);
  }
}

export { fetchChartData };
