import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export function ClientActivityChart({ clients }) {
  const chartData = {
    labels: clients?.map((c) => c.username) || ["Client 1", "Client 2", "Client 3"],
    datasets: [
      {
        label: "Call Volume",
        data: clients?.map((c) => c.call_volume) || [2500, 3200, 1800],
        backgroundColor: ["#3b82f6", "#10b981", "#f59e0b"],
        borderColor: ["#1e40af", "#059669", "#d97706"],
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
          maintainAspectRatio: true,
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: true,
              text: "Top Clients by Call Volume",
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
