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
  const entries = Object.entries(data || {});

  const chartData = {
    labels: entries.length ? entries.map(([slot]) => slot.replace(/_/g, " ")) : ["No data"],
    datasets: [
      {
        label: "Response rate %",
        data: entries.length ? entries.map(([, rate]) => (Number(rate) || 0) * 100) : [0],
        borderColor: "#03d4ff",
        backgroundColor: "rgba(3, 212, 255, 0.18)",
        tension: 0.4,
        borderWidth: 2,
        pointBackgroundColor: "#7fffd4",
        fill: true,
      },
    ],
  };

  return (
    <div className="chart-container">
      <Line
        data={chartData}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: {
                color: "#d9ebff",
                boxWidth: 12,
              },
            },
            title: {
              display: true,
              text: "Response Rate by Time",
              color: "#d9ebff",
            },
          },
          scales: {
            x: {
              ticks: { color: "#8eaed3", maxRotation: 0 },
              grid: { color: "rgba(23, 60, 103, 0.35)" },
            },
            y: {
              beginAtZero: true,
              suggestedMax: 100,
              ticks: {
                color: "#8eaed3",
                callback: (value) => `${value}%`,
              },
              grid: { color: "rgba(23, 60, 103, 0.35)" },
            },
          },
        }}
      />
    </div>
  );
}
