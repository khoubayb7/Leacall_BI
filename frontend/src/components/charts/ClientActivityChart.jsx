import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export function ClientActivityChart({ distribution = {} }) {
  const entries = Object.entries(distribution || {});

  const chartData = {
    labels: entries.length ? entries.map(([key]) => key.replace(/_/g, " ")) : ["No data"],
    datasets: [
      {
        label: "Lead count",
        data: entries.length ? entries.map(([, count]) => Number(count) || 0) : [0],
        backgroundColor: "rgba(3, 212, 255, 0.35)",
        borderColor: "#03d4ff",
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="chart-container">
      <Bar
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
              text: "Lead Status Distribution",
              color: "#d9ebff",
            },
          },
          scales: {
            x: {
              ticks: {
                color: "#8eaed3",
                maxRotation: 20,
                minRotation: 0,
              },
              grid: { color: "rgba(23, 60, 103, 0.35)" },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: "#8eaed3",
                precision: 0,
              },
              grid: { color: "rgba(23, 60, 103, 0.35)" },
            },
          },
        }}
      />
    </div>
  );
}
