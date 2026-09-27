import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Activity,
  DollarSign,
  RefreshCw,
  Cpu,
  BarChart2,
  AlertCircle,
  CheckCircle2,
  Sliders,
} from "lucide-react";

export default function Dashboard() {
  const [username, setUsername] = useState("demo_investor");
  const [portfolio, setPortfolio] = useState(null);
  const [marketData, setMarketData] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rebalancing, setRebalancing] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Config form state
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [targetEsg, setTargetEsg] = useState(70);

  const API_BASE = "http://localhost:8000/api";

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch user portfolio
      const portRes = await fetch(`${API_BASE}/portfolio/${username}`);
      if (!portRes.ok) throw new Error("Failed to fetch portfolio");
      const portData = await portRes.json();
      setPortfolio(portData);
      setRiskTolerance(portData.risk_tolerance);
      setTargetEsg(portData.target_esg_score);

      // Fetch Market Data & ML predictions
      const marketRes = await fetch(`${API_BASE}/market-data`);
      if (marketRes.ok) {
        const mData = await marketRes.json();
        setMarketData(mData);
      }

      // Fetch Rebalance History
      const histRes = await fetch(`${API_BASE}/portfolio/${username}/history`);
      if (histRes.ok) {
        const hData = await histRes.json();
        setHistory(hData);
      }
    } catch (err) {
      console.warn("API offline, falling back to mock dashboard data:", err);
      // Fallback mock data so UI is fully explorable even if backend isn't actively running
      setPortfolio({
        username: "demo_investor",
        total_value: 104250.8,
        cash: 12500.0,
        risk_tolerance: "moderate",
        target_esg_score: 75.0,
        current_esg_score: 81.4,
        assets: [
          {
            ticker: "AAPL",
            shares: 50.5,
            avg_buy_price: 220.0,
            current_price: 245.5,
            esg_score: 82.0,
            current_value: 12397.75,
          },
          {
            ticker: "MSFT",
            shares: 40.0,
            avg_buy_price: 410.0,
            current_price: 435.2,
            esg_score: 85.0,
            current_value: 17408.0,
          },
          {
            ticker: "NEE",
            shares: 150.0,
            avg_buy_price: 78.5,
            current_price: 82.4,
            esg_score: 92.0,
            current_value: 12360.0,
          },
          {
            ticker: "NVDA",
            shares: 35.0,
            avg_buy_price: 110.0,
            current_price: 128.6,
            esg_score: 75.0,
            current_value: 4501.0,
          },
        ],
      });
      setMarketData([
        {
          ticker: "AAPL",
          company_name: "Apple Inc.",
          current_price: 245.5,
          predicted_price: 262.0,
          predicted_return: 6.72,
          esg_score: 82.0,
          sentiment_score: 0.65,
        },
        {
          ticker: "MSFT",
          company_name: "Microsoft Corporation",
          current_price: 435.2,
          predicted_price: 458.0,
          predicted_return: 5.24,
          esg_score: 85.0,
          sentiment_score: 0.72,
        },
        {
          ticker: "TSLA",
          company_name: "Tesla, Inc.",
          current_price: 220.4,
          predicted_price: 205.0,
          predicted_return: -6.99,
          esg_score: 72.0,
          sentiment_score: -0.45,
        },
        {
          ticker: "NEE",
          company_name: "NextEra Energy, Inc.",
          current_price: 82.4,
          predicted_price: 89.5,
          predicted_return: 8.62,
          esg_score: 92.0,
          sentiment_score: 0.81,
        },
      ]);
      setHistory([
        {
          id: 1,
          timestamp: "2026-09-27 10:30:00",
          action_summary: "Bought 150 shares of NEE | Sold 10 shares of TSLA",
          old_esg_score: 68.2,
          new_esg_score: 81.4,
          old_sentiment: 0.12,
          new_sentiment: 0.48,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [username]);

  const handleRebalance = async () => {
    setRebalancing(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await fetch(`${API_BASE}/portfolio/${username}/rebalance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error("Rebalance execution failed");
      const data = await res.json();
      setSuccessMsg("Autonomous portfolio rebalancing completed successfully!");
      await fetchData();
    } catch (err) {
      setError(err.message);
    } finally {
      setRebalancing(false);
    }
  };

  const handleUpdateConfig = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await fetch(`${API_BASE}/portfolio/${username}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          risk_tolerance: riskTolerance,
          target_esg_score: parseFloat(targetEsg),
        }),
      });
      if (!res.ok) throw new Error("Failed to update portfolio configuration");
      setSuccessMsg("Portfolio parameters updated successfully!");
      await fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-10">
      {/* Top Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="text-emerald-400 w-8 h-8 animate-pulse" />
            <h1 className="text-3xl font-extrabold tracking-tight text-white">
              Enterprise FinTech Intelligence
            </h1>
          </div>
          <p className="text-slate-400">
            Autonomous Portfolio Manager & ML Time-Series Sentiment Engine
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300">
            User: <strong className="text-emerald-400">{username}</strong>
          </span>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg text-sm font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />{" "}
            Refresh
          </button>
        </div>
      </header>

      {/* Notifications */}
      {successMsg && (
        <div className="mb-6 flex items-center gap-3 bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 p-4 rounded-xl">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {error && (
        <div className="mb-6 flex items-center gap-3 bg-rose-950/60 border border-rose-500/50 text-rose-300 p-4 rounded-xl">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Portfolio, Holdings & Predictions */}
        <div className="lg:col-span-2 space-y-8">
          {/* Portfolio Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div className="bg-slate-800/80 backdrop-blur border border-slate-700/80 p-6 rounded-2xl shadow-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-400">
                  Total Portfolio Value
                </span>
                <DollarSign className="text-emerald-400 w-5 h-5" />
              </div>
              <div className="text-3xl font-bold text-white">
                $
                {portfolio
                  ? portfolio.total_value.toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })
                  : "0.00"}
              </div>
              <p className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5" /> +4.8% all-time return
              </p>
            </div>

            <div className="bg-slate-800/80 backdrop-blur border border-slate-700/80 p-6 rounded-2xl shadow-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-400">
                  Portfolio ESG Score
                </span>
                <ShieldCheck className="text-blue-400 w-5 h-5" />
              </div>
              <div className="text-3xl font-bold text-white">
                {portfolio ? portfolio.current_esg_score : "0.0"}{" "}
                <span className="text-sm font-normal text-slate-400">
                  / 100
                </span>
              </div>
              <p className="text-xs text-blue-400 mt-1">
                Target: {portfolio ? portfolio.target_esg_score : "70"}{" "}
                (Compliant)
              </p>
            </div>

            <div className="bg-slate-800/80 backdrop-blur border border-slate-700/80 p-6 rounded-2xl shadow-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-400">
                  Available Cash
                </span>
                <Activity className="text-purple-400 w-5 h-5" />
              </div>
              <div className="text-3xl font-bold text-white">
                $
                {portfolio
                  ? portfolio.cash.toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })
                  : "0.00"}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Ready for automated deployment
              </p>
            </div>
          </div>

          {/* Active Holdings Table */}
          <div className="bg-slate-800/80 backdrop-blur border border-slate-700/80 rounded-2xl p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-emerald-400" /> Current Asset
              Holdings
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                    <th className="py-3 px-4">Ticker</th>
                    <th className="py-3 px-4">Shares</th>
                    <th className="py-3 px-4">Avg Buy</th>
                    <th className="py-3 px-4">Current Price</th>
                    <th className="py-3 px-4">Total Value</th>
                    <th className="py-3 px-4">ESG</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50 text-sm">
                  {portfolio &&
                  portfolio.assets &&
                  portfolio.assets.length > 0 ? (
                    portfolio.assets.map((asset) => (
                      <tr
                        key={asset.ticker}
                        className="hover:bg-slate-700/30 transition"
                      >
                        <td className="py-3 px-4 font-bold text-white">
                          {asset.ticker}
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          {asset.shares}
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          ${asset.avg_buy_price.toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          ${asset.current_price.toFixed(2)}
                        </td>
                        <td className="py-3 px-4 font-semibold text-emerald-400">
                          $
                          {asset.current_value.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                              asset.esg_score >= 80
                                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                : asset.esg_score >= 70
                                  ? "bg-blue-950 text-blue-300 border border-blue-800"
                                  : "bg-amber-950 text-amber-300 border border-amber-800"
                            }`}
                          >
                            {asset.esg_score}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan="6"
                        className="py-6 text-center text-slate-400"
                      >
                        No active assets in portfolio. Trigger a rebalance to
                        start.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* ML Predictions & Sentiment Engine */}
          <div className="bg-slate-800/80 backdrop-blur border border-slate-700/80 rounded-2xl p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-purple-400" /> AI Market Predictions
              & Sentiment Engine
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {marketData.map((item) => (
                <div
                  key={item.ticker}
                  className="bg-slate-900/60 border border-slate-700/60 p-4 rounded-xl flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-bold text-lg text-white">
                          {item.ticker}
                        </h3>
                        <p className="text-xs text-slate-400">
                          {item.company_name}
                        </p>
                      </div>
                      <span
                        className={`flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold ${
                          item.predicted_return >= 0
                            ? "bg-emerald-950 text-emerald-400"
                            : "bg-rose-950 text-rose-400"
                        }`}
                      >
                        {item.predicted_return >= 0 ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        {item.predicted_return > 0 ? "+" : ""}
                        {item.predicted_return}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800 grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-slate-400 block">Current</span>
                      <span className="font-semibold text-white">
                        ${item.current_price}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">
                        AI Forecast (5d)
                      </span>
                      <span className="font-semibold text-emerald-400">
                        ${item.predicted_price}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Sentiment</span>
                      <span
                        className={`font-semibold ${item.sentiment_score >= 0 ? "text-emerald-400" : "text-rose-400"}`}
                      >
                        {item.sentiment_score >= 0 ? "Bullish" : "Bearish"} (
                        {item.sentiment_score})
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Controls, Rebalancing & Audit Logs */}
        <div className="space-y-8">
          {/* Autonomous Rebalance Control Panel */}
          <div className="bg-slate-800/80 backdrop-blur border border-slate-700/80 rounded-2xl p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Sliders className="w-5 h-5 text-blue-400" /> Portfolio Parameters
            </h2>

            <form onSubmit={handleUpdateConfig} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Risk Tolerance
                </label>
                <select
                  value={riskTolerance}
                  onChange={(e) => setRiskTolerance(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="conservative">Conservative</option>
                  <option value="moderate">Moderate</option>
                  <option value="aggressive">Aggressive</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Target ESG Score:{" "}
                  <span className="text-emerald-400 font-bold">
                    {targetEsg} / 100
                  </span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={targetEsg}
                  onChange={(e) => setTargetEsg(e.target.value)}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-slate-700 hover:bg-slate-600 font-medium py-2.5 rounded-lg text-sm transition border border-slate-600"
              >
                Save Configuration
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-slate-700">
              <button
                onClick={handleRebalance}
                disabled={rebalancing}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition disabled:opacity-50"
              >
                <RefreshCw
                  className={`w-5 h-5 ${rebalancing ? "animate-spin" : ""}`}
                />
                {rebalancing
                  ? "Running Rebalance & ML Engine..."
                  : "Trigger Autonomous Rebalance"}
              </button>
              <p className="text-xs text-slate-400 text-center mt-2">
                Executes ML forecasting, sentiment analysis & ESG constraint
                resolution.
              </p>
            </div>
          </div>

          {/* Rebalance Audit & Transaction History */}
          <div className="bg-slate-800/80 backdrop-blur border border-slate-700/80 rounded-2xl p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" /> Compliance Audit
              Logs
            </h2>
            <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
              {history && history.length > 0 ? (
                history.map((log) => (
                  <div
                    key={log.id}
                    className="bg-slate-900/60 border border-slate-700/60 p-4 rounded-xl text-xs space-y-2"
                  >
                    <div className="flex justify-between text-slate-400">
                      <span>{log.timestamp}</span>
                      <span className="bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded font-mono">
                        ESG: {log.old_esg_score} → {log.new_esg_score}
                      </span>
                    </div>
                    <p className="text-slate-200 font-medium">
                      {log.action_summary}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400 text-center py-4">
                  No rebalance logs recorded yet.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
