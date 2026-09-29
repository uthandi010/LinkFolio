import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import { NavBar } from "../components/NavBar";
import * as analyticsApi from "../api/analytics";
import { ApiError } from "../api/client";

function formatShortDate(isoDate) {
  const d = new Date(`${isoDate}T00:00:00`);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function LineTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{formatShortDate(label)}</div>
      <div className="chart-tooltip-value">{payload[0].value} clicks</div>
    </div>
  );
}

function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{row.title}</div>
      <div className="chart-tooltip-value">{row.clicks} clicks</div>
    </div>
  );
}

export function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    analyticsApi
      .getAnalyticsSummary()
      .then(setSummary)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load analytics."));
  }, []);

  if (error) {
    return (
      <div>
        <NavBar />
        <main className="page-content">
          <div className="form-error" role="alert">
            {error}
          </div>
        </main>
      </div>
    );
  }

  if (!summary) {
    return (
      <div>
        <NavBar />
        <main className="page-content">
          <p className="muted">Loading analytics...</p>
        </main>
      </div>
    );
  }

  const dailyData = summary.clicks_by_day.map((row) => ({ date: row.date, clicks: row.clicks }));
  const linkData = summary.clicks_by_link.slice(0, 8);

  return (
    <div>
      <NavBar />
      <main className="page-content">
        <div className="page-header">
          <h1>Analytics</h1>
          <p>How your links are performing.</p>
        </div>

        <div className="stat-tiles">
          <div className="stat-tile">
            <span className="stat-label">Total clicks</span>
            <span className="stat-value">{summary.total_clicks.toLocaleString()}</span>
          </div>
          <div className="stat-tile">
            <span className="stat-label">Links</span>
            <span className="stat-value">{summary.total_links}</span>
          </div>
          <div className="stat-tile">
            <span className="stat-label">Avg. clicks / link</span>
            <span className="stat-value">
              {summary.total_links > 0 ? (summary.total_clicks / summary.total_links).toFixed(1) : "0"}
            </span>
          </div>
        </div>

        <div className="chart-card">
          <h2>Clicks, last 30 days</h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={dailyData} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={formatShortDate}
                tick={{ fill: "var(--chart-muted)", fontSize: 12 }}
                axisLine={{ stroke: "var(--chart-axis)" }}
                tickLine={false}
                interval={4}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: "var(--chart-muted)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={28}
              />
              <Tooltip content={<LineTooltip />} />
              <Area
                type="monotone"
                dataKey="clicks"
                stroke="var(--chart-series-1)"
                strokeWidth={2}
                fill="var(--chart-series-1)"
                fillOpacity={0.1}
                activeDot={{ r: 4, stroke: "var(--chart-surface)", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h2>Clicks by link</h2>
          {linkData.length === 0 ? (
            <p className="muted">No clicks yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(120, linkData.length * 44)}>
              <BarChart
                data={linkData}
                layout="vertical"
                margin={{ top: 4, right: 32, bottom: 4, left: 4 }}
                barSize={20}
              >
                <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
                <XAxis type="number" allowDecimals={false} hide />
                <YAxis
                  type="category"
                  dataKey="title"
                  tick={{ fill: "var(--chart-text)", fontSize: 13 }}
                  axisLine={false}
                  tickLine={false}
                  width={120}
                />
                <Tooltip content={<BarTooltip />} cursor={{ fill: "var(--chart-grid)" }} />
                <Bar dataKey="clicks" fill="var(--chart-series-1)" radius={[0, 4, 4, 0]}>
                  <LabelList dataKey="clicks" position="right" fill="var(--chart-text)" fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </main>
    </div>
  );
}
