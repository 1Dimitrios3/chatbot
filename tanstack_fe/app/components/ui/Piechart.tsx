import React from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, ChartData } from 'chart.js';

// Register necessary chart elements
Chart.register(ArcElement, Tooltip, Legend);

interface PieData {
  labels: string[];
  values: number[];
}

interface PieChartProps {
  pieData: PieData;
}

const PieChart: React.FC<PieChartProps> = ({ pieData }) => {
  const data: ChartData<'pie', number[], unknown> = {
    labels: pieData.labels,
    datasets: [
      {
        data: pieData.values,
        backgroundColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56', 
          '#4BC0C0', 
          '#9966FF',
          '#FF9F40',
          '#00C49F',
          '#C9CBCF'
        ],
      },
    ],
  };

  const options = {
    maintainAspectRatio: false,
    plugins: {
      datalabels: {
        color: 'white',
        font: {
          weight: 'bold',
          size: 12,
        },
        formatter: (value: any, context: any) => {
          return context.chart.data.labels[context.dataIndex];
        },
      },
      title: {
        display: true,
        text: 'Pie Chart Title',
        color: 'white',
        font: {
          size: 16,
        },
      },
      legend: {
        labels: {
          color: 'white',
        },
      },
    },
  };

  return (
    <div style={{ width: '400px', height: '400px' }}>
      <Pie data={data} options={options} />
    </div>
  );
};

export default PieChart;
