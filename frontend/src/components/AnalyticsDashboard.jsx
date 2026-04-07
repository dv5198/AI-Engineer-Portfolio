import React, { useEffect, useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  BarChart, Bar, Cell, PieChart, Pie
} from 'recharts';

const AnalyticsDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/platform/summary/')
      .then(res => res.json())
      .then(data => {
        setAnalytics(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="h-64 flex items-center justify-center font-mono text-xs text-warmBrown/40">Calculating metrics...</div>;
  if (!analytics) return <div className="h-64 flex items-center justify-center font-mono text-xs text-red-400">Failed to load analytics infrastructure.</div>;

  return (
    <div className="space-y-12">
      {/* High Level Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: "Total Visits", value: analytics.total_visits, color: "text-warmBrown" },
          { label: "Unique Visitors", value: analytics.unique_visitors, color: "text-accent" },
          { label: "Resume Pulls", value: analytics.resume_downloads, color: "text-warmBrown" },
          { label: "Form Leads", value: analytics.messages_total, color: "text-accent" }
        ].map((stat, i) => (
          <div key={i} className="bg-white border border-warmBrown/5 p-6 shadow-sm">
            <p className="font-mono text-[9px] uppercase tracking-widest text-warmBrown/40 mb-2">{stat.label}</p>
            <p className={`text-4xl font-serif ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Daily Traffic */}
        <div className="bg-white border border-warmBrown/5 p-8 shadow-sm h-[400px]">
          <h3 className="font-serif text-xl mb-8">Traffic Velocity</h3>
          <ResponsiveContainer width="100%" height="80%">
            <LineChart data={analytics.traffic_over_time}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0ebe0" />
              <XAxis 
                dataKey="date" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 9, fontFamily: 'DM Mono', fill: '#7a6a55' }}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 9, fontFamily: 'DM Mono', fill: '#7a6a55' }}
              />
              <Tooltip 
                contentStyle={{ border: 'none', backgroundColor: '#1a1510', color: '#f0ebe0', fontSize: '10px', fontFamily: 'DM Mono' }}
                itemStyle={{ color: '#b89868' }}
              />
              <Line 
                type="monotone" 
                dataKey="visits" 
                stroke="#b89868" 
                strokeWidth={2} 
                dot={{ fill: '#b89868', r: 4 }} 
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Event Distribution */}
        <div className="bg-white border border-warmBrown/5 p-8 shadow-sm h-[400px]">
          <h3 className="font-serif text-xl mb-8">Interaction Mix</h3>
          <ResponsiveContainer width="100%" height="80%">
            <BarChart data={[
              { name: 'Views', value: analytics.total_visits },
              { name: 'Downloads', value: analytics.resume_downloads },
              { name: 'Messages', value: analytics.messages_total }
            ]}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0ebe0" />
              <XAxis 
                dataKey="name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 9, fontFamily: 'DM Mono', fill: '#7a6a55' }}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 9, fontFamily: 'DM Mono', fill: '#7a6a55' }}
              />
              <Tooltip 
                cursor={{ fill: '#f0ebe0' }}
                contentStyle={{ border: 'none', backgroundColor: '#1a1510', color: '#f0ebe0', fontSize: '10px', fontFamily: 'DM Mono' }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                { [0,1,2].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#b89868' : '#4a3a28'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
