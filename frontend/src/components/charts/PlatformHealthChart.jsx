import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export function PlatformHealthChart({ data }) {
  const chartData = {
    labels: ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"],
    datasets: [
      {
        label: "API Response Time (ms)",
        data: data?.responseTimeData || [45, 52, 48, 61, 55, 49],
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        tension: 0.4,
        borderWidth: 2,
      },
      {
        label: "Error Rate (%)",
        data: data?.errorRateData || [2, 1.8, 2.2, 1.5, 2.1, 1.9],
        borderColor: "#ef4444",
        backgroundColor: "rgba(239, 68, 68, 0.1)",
        tension: 0.4,
        borderWidth: 2,
      },
    ],
  };

  return (
    <div className="chart-container">
      <Line
        data={chartData}
        options={{
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: true,
              text: "API Performance Over Time",
            },
          },
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        }}
      />
    </div>
  );
}
