import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  LogarithmicScale
} from 'chart.js';

// Register the necessary Chart.js components.
Chart.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, LogarithmicScale);

interface BarChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor: string;
  }>;
}

interface BarChartProps {
  barData: BarChartData;
}

const BarChart: React.FC<BarChartProps> = ({ barData }) => {
  const data: ChartData<'bar', number[], string> = {
    labels: barData.labels,
    datasets: barData.datasets.map(dataset => ({
      label: dataset.label,
      data: dataset.data,
      backgroundColor: dataset.backgroundColor
    }))
  };

  // Chart configuration options.
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: 'white',
        },
      },
      title: {
        display: true,
        text: 'Numeric Summary Bar Chart',
        color: 'white',
      },
    },
    scales: {
      y: {
        type: 'logarithmic' as const, // Set the scale to logarithmic
        beginAtZero: false,
        ticks: {
          // Optional: Format ticks to display as plain numbers
          callback: function(value: any) {
            return Number(value).toLocaleString();
          },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.2)',
        },
      },
      x: {
        ticks: { color: 'white' },
        grid: { color: 'rgba(255, 255, 255, 0.2)' },
      },
    },
  };
  

  return (
    <div style={{ width: '600px', height: '400px' }}>
      <Bar data={data} options={options} />
    </div>
  );
};

export default BarChart;
