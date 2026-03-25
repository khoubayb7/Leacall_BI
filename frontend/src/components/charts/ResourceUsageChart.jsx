import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

export function ResourceUsageChart({ talkToListenRatio = 0 }) {
  const talkPercent = Math.max(0, Math.min(100, (Number(talkToListenRatio) || 0) * 100));

  return (
    <div className="chart-container">
      <Doughnut
        data={{
          labels: ["Talk", "Listen"],
          datasets: [
            {
              data: [talkPercent, 100 - talkPercent],
              backgroundColor: ["#3b82f6", "rgba(59, 130, 246, 0.2)"],
              borderColor: "#1e40af",
              borderWidth: 2,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          cutout: "52%",
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
              text: "Talk vs Listen Ratio",
              color: "#d9ebff",
            },
          },
        }}
      />
    </div>
  );
}
