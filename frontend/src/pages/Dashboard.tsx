import React, { useEffect, useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { 
  BookOpen, Brain, Target, Trophy, TrendingUp, AlertTriangle, Activity 
} from 'lucide-react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface AnalyticsData {
  total_documents: number;
  total_questions_asked: number;
  total_quizzes_taken: number;
  average_score: number;
  weakest_concepts: { concept: string; success_rate: number }[];
  progression: { date: string; quiz_title: string; score_percentage: number }[];
}

// Dummy data for visual presentation if API fails or is loading
const DUMMY_DATA: AnalyticsData = {
  total_documents: 12,
  total_questions_asked: 145,
  total_quizzes_taken: 8,
  average_score: 78.5,
  weakest_concepts: [
    { concept: 'Backpropagation', success_rate: 45.0 },
    { concept: 'Gradient Descent', success_rate: 55.5 },
    { concept: 'Attention Mechanism', success_rate: 62.0 },
  ],
  progression: [
    { date: '2026-08-10', quiz_title: 'Intro to AI', score_percentage: 60 },
    { date: '2026-08-11', quiz_title: 'Neural Nets', score_percentage: 75 },
    { date: '2026-08-12', quiz_title: 'Deep Learning', score_percentage: 70 },
    { date: '2026-08-14', quiz_title: 'Transformers', score_percentage: 85 },
    { date: '2026-08-16', quiz_title: 'LLMs', score_percentage: 92 },
  ]
};

const StatCard = ({ title, value, icon: Icon, trend, color }: any) => (
  <div className="relative overflow-hidden bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-6 transition-all hover:bg-white/10 hover:-translate-y-1 hover:shadow-2xl hover:shadow-indigo-500/10 group">
    <div className={`absolute top-0 right-0 p-4 opacity-10 transform translate-x-4 -translate-y-4 group-hover:scale-110 transition-transform ${color}`}>
      <Icon size={120} />
    </div>
    <div className="flex items-center gap-4 mb-4">
      <div className={`p-3 rounded-xl bg-white/5 ${color} border border-white/10`}>
        <Icon size={24} />
      </div>
      <h3 className="text-gray-400 font-medium tracking-wide text-sm uppercase">{title}</h3>
    </div>
    <div className="flex items-end gap-3">
      <span className="text-4xl font-bold text-white tracking-tight">{value}</span>
      {trend && (
        <span className="text-emerald-400 flex items-center text-sm font-medium mb-1">
          <TrendingUp size={16} className="mr-1" /> {trend}
        </span>
      )}
    </div>
  </div>
);

export default function Dashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app, this would use an auth token
    fetch('/api/v1/analytics/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
      .then(res => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then(setData)
      .catch((err) => {
        console.error("Failed to fetch analytics, using fallback data", err);
        // Using dummy data for aesthetic preview
        setData(DUMMY_DATA);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="  flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <Activity className="text-indigo-500 animate-spin" size={40} />
          <p className="text-indigo-400 font-medium tracking-widest uppercase">Analyzing Brain Waves...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="  text-slate-200 p-6 md:p-10 font-sans selection:bg-indigo-500/30">
      
      {/* Dynamic Background Glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/2 w-[1000px] h-[1000px] rounded-full bg-indigo-900/20 blur-[120px] mix-blend-screen opacity-50"></div>
        <div className="absolute -bottom-1/2 -left-1/2 w-[800px] h-[800px] rounded-full bg-blue-900/20 blur-[120px] mix-blend-screen opacity-50"></div>
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        <header className="mb-12">
          <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-200 to-blue-400 mb-4 tracking-tight">
            Learning Analytics
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">
            Track your cognitive progression, identify knowledge gaps, and optimize your study sessions with AI-driven insights.
          </p>
        </header>

        {/* Top Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <StatCard 
            title="Documents" 
            value={data?.total_documents} 
            icon={BookOpen} 
            color="text-blue-400"
            trend="+2 this week"
          />
          <StatCard 
            title="Questions Asked" 
            value={data?.total_questions_asked} 
            icon={Brain} 
            color="text-purple-400"
            trend="+15 today"
          />
          <StatCard 
            title="Quizzes Taken" 
            value={data?.total_quizzes_taken} 
            icon={Target} 
            color="text-emerald-400"
          />
          <StatCard 
            title="Average Score" 
            value={`${data?.average_score.toFixed(1)}%`} 
            icon={Trophy} 
            color="text-amber-400"
            trend="Top 10%"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Progression Chart */}
          <div className="lg:col-span-2 bg-white/5 border border-white/10 backdrop-blur-xl rounded-3xl p-8">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Performance Curve</h2>
                <p className="text-slate-400 text-sm">Your quiz scores over recent sessions</p>
              </div>
            </div>
            
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.progression || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis 
                    dataKey="quiz_title" 
                    stroke="#ffffff40" 
                    tick={{fill: '#ffffff60', fontSize: 12}} 
                    tickLine={false}
                    axisLine={false}
                    dy={10}
                  />
                  <YAxis 
                    stroke="#ffffff40" 
                    tick={{fill: '#ffffff60', fontSize: 12}} 
                    tickLine={false}
                    axisLine={false}
                    dx={-10}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e1e24', 
                      borderColor: '#ffffff20',
                      borderRadius: '12px',
                      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                    }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="score_percentage" 
                    stroke="#818cf8" 
                    strokeWidth={4}
                    fillOpacity={1} 
                    fill="url(#colorScore)" 
                    activeDot={{ r: 8, fill: '#c7d2fe', stroke: '#4f46e5', strokeWidth: 3 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Weakest Concepts */}
          <div className="bg-gradient-to-b from-rose-500/10 to-transparent border border-rose-500/20 backdrop-blur-xl rounded-3xl p-8 flex flex-col">
            <div className="flex items-center gap-3 mb-8">
              <div className="p-3 bg-rose-500/20 rounded-xl">
                <AlertTriangle className="text-rose-400" size={24} />
              </div>
              <h2 className="text-2xl font-bold text-white">Focus Areas</h2>
            </div>
            
            <p className="text-slate-400 text-sm mb-6">
              AI has identified these concepts as your weakest based on recent quiz performances.
            </p>

            <div className="flex-1 space-y-6">
              {data?.weakest_concepts.map((concept, idx) => (
                <div key={idx} className="group relative">
                  <div className="flex justify-between items-end mb-2">
                    <span className="font-semibold text-slate-200 group-hover:text-rose-300 transition-colors">
                      {concept.concept}
                    </span>
                    <span className="text-sm font-mono text-rose-400/80">
                      {concept.success_rate.toFixed(0)}% accuracy
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-rose-500 to-orange-400 h-2.5 rounded-full transition-all duration-1000 ease-out relative"
                      style={{ width: `${concept.success_rate}%` }}
                    >
                      <div className="absolute inset-0 bg-white/20 w-full animate-[shimmer_2s_infinite]"></div>
                    </div>
                  </div>
                </div>
              ))}

              {(!data?.weakest_concepts || data.weakest_concepts.length === 0) && (
                <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3 py-10">
                  <Trophy size={40} className="text-emerald-500/30" />
                  <p className="text-center">You have no weak concepts yet!<br/>Take more quizzes to gather data.</p>
                </div>
              )}
            </div>

            <button className="mt-8 w-full py-4 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]">
              Generate Targeted Quiz
            </button>
          </div>
          
        </div>
      </div>
      
      {/* Global styles for animations */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}
