import { useEffect, useState } from 'react';
import { 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { 
  BookOpen, Brain, Target, Trophy, TrendingUp, AlertTriangle, Activity, Download, Filter, Loader2 
} from 'lucide-react';
import { apiGet } from '../lib/api';

const BASE_URL = 'http://localhost:8000/api/v1';

interface AnalyticsData {
  total_documents: number;
  total_questions_asked: number;
  total_quizzes_taken: number;
  average_score: number;
  weakest_concepts: { concept: string; success_rate: number }[];
  progression: { date: string; quiz_title: string; score_percentage: number }[];
  streak_days: number;
}

const StatCard = ({ title, value, icon: Icon, trend }: any) => (
  <div className="bg-[#0A0A0A] border border-[#222] rounded-xl p-6 relative overflow-hidden group">
    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
      <Icon size={100} />
    </div>
    <div className="flex items-center gap-3 mb-4">
      <div className="p-2 rounded-lg bg-[#111] border border-[#333] text-[#A1A1AA]">
        <Icon size={20} />
      </div>
      <h3 className="text-[#A1A1AA] font-medium text-sm tracking-wide">{title}</h3>
    </div>
    <div className="flex items-end gap-3">
      <span className="text-4xl font-semibold text-white tracking-tight">{value}</span>
      {trend && (
        <span className="text-white flex items-center text-sm font-medium mb-1 border border-[#333] rounded px-2 py-0.5 bg-[#111]">
          <TrendingUp size={14} className="mr-1" /> {trend}
        </span>
      )}
    </div>
  </div>
);

export default function Dashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [docs, setDocs] = useState<{id: string, title: string}[]>([]);
  
  // Filters
  const [docFilter, setDocFilter] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  useEffect(() => {
    apiGet<any[]>('/documents/').then(res => setDocs(res)).catch(console.error);
    fetchData();
  }, [docFilter, fromDate, toDate]);

  const fetchData = () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    const params = new URLSearchParams();
    if (docFilter) params.append('document_id', docFilter);
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    fetch(`${BASE_URL}/knowledge/analytics/?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(res => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then(setData)
      .catch((err) => {
        console.error("Failed to fetch analytics", err);
      })
      .finally(() => setLoading(false));
  };

  const handleExportCSV = () => {
    const token = localStorage.getItem('access_token');
    const params = new URLSearchParams({ export: 'csv' });
    if (docFilter) params.append('document_id', docFilter);
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    fetch(`${BASE_URL}/knowledge/analytics/?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_${new Date().toISOString().slice(0,10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    })
    .catch(console.error);
  };

  if (!data && loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-8rem)]">
        <div className="flex flex-col items-center gap-4">
          <Activity className="text-white animate-spin" size={32} />
          <p className="text-[#A1A1AA] font-medium text-sm">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="text-white">
      <div className="max-w-7xl mx-auto relative z-10">
        <header className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[#222] pb-8">
          <div>
            <h1 className="text-3xl font-semibold text-white tracking-tight mb-2">
              Learning Analytics
            </h1>
            <p className="text-[#A1A1AA] text-sm max-w-2xl">
              Track your cognitive progression and identify knowledge gaps.
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-[#0A0A0A] p-1.5 rounded-lg border border-[#222]">
              <Filter size={16} className="text-[#52525B] ml-2" />
              <select 
                value={docFilter} 
                onChange={e => setDocFilter(e.target.value)}
                className="bg-transparent border-none text-sm text-[#EDEDED] focus:outline-none focus:ring-0 w-36"
              >
                <option value="">All Documents</option>
                {docs.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}
              </select>
              <div className="w-px h-5 bg-[#333]"></div>
              <input 
                type="date"
                value={fromDate}
                onChange={e => setFromDate(e.target.value)}
                className="bg-transparent border-none text-sm text-[#EDEDED] focus:outline-none [color-scheme:dark]"
              />
              <span className="text-[#52525B]">-</span>
              <input 
                type="date"
                value={toDate}
                onChange={e => setToDate(e.target.value)}
                className="bg-transparent border-none text-sm text-[#EDEDED] focus:outline-none [color-scheme:dark]"
              />
            </div>
            <button 
              onClick={handleExportCSV}
              className="minimal-button-secondary py-1.5 flex items-center gap-2"
            >
              <Download size={16} /> Export
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard 
            title="Documents" 
            value={data?.total_documents || 0} 
            icon={BookOpen} 
          />
          <StatCard 
            title="Questions Asked" 
            value={data?.total_questions_asked || 0} 
            icon={Brain} 
          />
          <StatCard 
            title="Quizzes Taken" 
            value={data?.total_quizzes_taken || 0} 
            icon={Target} 
          />
          <StatCard 
            title="Average Score" 
            value={`${(data?.average_score || 0).toFixed(1)}%`} 
            icon={Trophy} 
            trend={data?.streak_days ? `${data.streak_days} Day Streak` : undefined}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 minimal-card p-8">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-xl font-semibold text-white mb-1">Performance Curve</h2>
                <p className="text-[#A1A1AA] text-sm">Your quiz scores over recent sessions</p>
              </div>
            </div>
            
            <div className="h-[300px] w-full relative">
              {loading && <div className="absolute inset-0 bg-[#0A0A0A]/80 flex items-center justify-center rounded-xl z-10">
                <Loader2 size={24} className="animate-spin text-[#A1A1AA]" />
              </div>}
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.progression || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ffffff" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#ffffff" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                  <XAxis 
                    dataKey="quiz_title" 
                    stroke="#555" 
                    tick={{fill: '#888', fontSize: 12}} 
                    tickLine={false}
                    axisLine={false}
                    dy={10}
                  />
                  <YAxis 
                    stroke="#555" 
                    tick={{fill: '#888', fontSize: 12}} 
                    tickLine={false}
                    axisLine={false}
                    dx={-10}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#111', 
                      borderColor: '#333',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="score_percentage" 
                    stroke="#fff" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorScore)" 
                    activeDot={{ r: 6, fill: '#000', stroke: '#fff', strokeWidth: 2 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="minimal-card p-8 flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-[#111] border border-[#333] rounded-lg">
                <AlertTriangle className="text-[#EDEDED]" size={20} />
              </div>
              <h2 className="text-xl font-semibold text-white">Focus Areas</h2>
            </div>
            
            <p className="text-[#A1A1AA] text-sm mb-6">
              AI identified these concepts as your weakest based on recent performance.
            </p>

            <div className="flex-1 space-y-6">
              {data?.weakest_concepts?.map((concept, idx) => (
                <div key={idx} className="group relative">
                  <div className="flex justify-between items-end mb-2">
                    <span className="font-medium text-white">
                      {concept.concept}
                    </span>
                    <span className="text-xs text-[#A1A1AA]">
                      {concept.success_rate.toFixed(0)}% accuracy
                    </span>
                  </div>
                  <div className="w-full bg-[#111] border border-[#222] rounded-full h-2 overflow-hidden">
                    <div 
                      className="bg-white h-2 rounded-full transition-all duration-1000 ease-out"
                      style={{ width: `${concept.success_rate}%` }}
                    />
                  </div>
                </div>
              ))}

              {(!data?.weakest_concepts || data.weakest_concepts.length === 0) && (
                <div className="flex flex-col items-center justify-center h-full text-[#52525B] gap-3 py-10">
                  <Trophy size={32} />
                  <p className="text-center text-sm">No weak concepts yet.<br/>Take more quizzes to gather data.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
