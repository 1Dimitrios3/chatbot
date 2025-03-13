// In your utils or a separate file, define the helper function:
import { baseUrl } from '~/config';
import { ConversationCard } from '~/types';
import { shouldShowPieChart } from '~/utils/regex';

async function fetchPieChartData(
  userMessage: string,
  sessionId: string,
  setConversations: React.Dispatch<React.SetStateAction<ConversationCard[]>>
) {
  if (!shouldShowPieChart(userMessage)) {
    return;
  }
  
  console.log("Storing chart data for session:", sessionId);
  try {
    const response = await fetch(`${baseUrl}/api/csv/chart-data/${sessionId}`);
    if (response.ok) {
      const chartData = await response.json();
      setConversations((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        updated[lastIndex] = {
          ...updated[lastIndex],
          assistant: {
            ...updated[lastIndex].assistant,
            chartData: chartData.pie_chart,
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

export { fetchPieChartData };
