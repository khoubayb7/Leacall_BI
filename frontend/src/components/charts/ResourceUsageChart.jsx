import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

export function ResourceUsageChart({ cpuUsage = 45, memoryUsage = 62, storageUsage = 35 }) {
  const chartData = {
    labels: ["CPU Available", "Memory Available", "Storage Available"],
    datasets: [
      {
        data: [100 - cpuUsage, 100 - memoryUsage, 100 - storageUsage],
        backgroundColor: ["rgba(59, 130, 246, 0.3)", "rgba(16, 185, 129, 0.3)", "rgba(245, 158, 11, 0.3)"],
        borderColor: ["#3b82f6", "#10b981", "#f59e0b"],
        borderWidth: 2,
      },
      {
        data: [cpuUsage, memoryUsage, storageUsage],
        backgroundColor: ["#3b82f6", "#10b981", "#f59e0b"],
        borderColor: ["#1e40af", "#059669", "#d97706"],
        borderWidth: 2,
      },
    ],
    labels: ["CPU Usage", "Memory Usage", "Storage Usage"],
  };

  return (
    <div className="chart-container">
      <Doughnut
        data={{
          labels: ["CPU Used", "CPU Available"],
          datasets: [
            {
              data: [cpuUsage, 100 - cpuUsage],
              backgroundColor: ["#3b82f6", "rgba(59, 130, 246, 0.2)"],
              borderColor: "#1e40af",
              borderWidth: 2,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              position: "bottom",
            },
            title: {
              display: true,
              text: "Resource Utilization",
            },
          },
        }}
      />
    </div>
  );
}
