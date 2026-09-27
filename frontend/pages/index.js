import React from 'react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-blue-900">FinTech Intelligence Dashboard</h1>
        <p className="text-gray-600">Autonomous Portfolio Management & Market Insights</p>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-md">
          <h2 className="text-xl font-semibold mb-4">Portfolio Summary</h2>
          <div className="text-3xl font-bold text-green-600">$1,240,500.00</div>
          <p className="text-sm text-gray-500">+2.4% from last month</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h2 className="text-xl font-semibold mb-4">ESG Score</h2>
          <div className="text-3xl font-bold text-blue-600">84/100</div>
          <p className="text-sm text-gray-500">Above sector average</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h2 className="text-xl font-semibold mb-4">Market Sentiment</h2>
          <div className="text-3xl font-bold text-orange-500">Bullish</div>
          <p className="text-sm text-gray-500">Based on real-time news analysis</p>
        </div>
      </main>
    </div>
  );
}
