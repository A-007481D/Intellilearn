import React, { useState, useEffect } from 'react';
import { apiGet, apiPost } from '../lib/api';
import { Brain, Play, CheckCircle2, XCircle, ArrowRight, ArrowLeft, Loader2 } from 'lucide-react';

interface Quiz {
  id: string;
  title: string;
  document_id: string;
  created_at: string;
}

export default function Quizzes() {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [docs, setDocs] = useState<{id: string, title: string}[]>([]);
  
  const [genDocId, setGenDocId] = useState('');
  const [genDiff, setGenDiff] = useState('medium');
  const [genNum, setGenNum] = useState(5);
  const [generating, setGenerating] = useState(false);

  const [activeQuiz, setActiveQuiz] = useState<any>(null); // Quiz data from API
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    fetchQuizzes();
    apiGet<any[]>('/knowledge/documents/').then(res => setDocs(res.filter(d => d.status === 'READY')));
  }, []);

  const fetchQuizzes = () => {
    apiGet<Quiz[]>('/knowledge/quizzes/').then(setQuizzes).catch(console.error);
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      await apiPost('/knowledge/quizzes/', {
        document_id: genDocId,
        difficulty: genDiff,
        num_questions: genNum
      });
      fetchQuizzes();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const startQuiz = async (id: string) => {
    try {
      const q = await apiGet<any>(`/knowledge/quizzes/${id}/`);
      setActiveQuiz(q);
      setCurrentQIndex(0);
      setAnswers({});
      setSubmitted(false);
    } catch (e) {
      console.error(e);
    }
  };

  if (activeQuiz) {
    if (submitted) {
      let correctCount = 0;
      activeQuiz.questions.forEach((q: any, i: number) => {
        if (answers[i] === q.correct_answer) correctCount++;
      });
      const score = Math.round((correctCount / activeQuiz.questions.length) * 100);

      return (
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center">
            <h2 className="text-3xl font-bold text-white mb-2">Quiz Complete!</h2>
            <div className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500 mb-6">
              {score}%
            </div>
            <p className="text-slate-400 mb-8">You got {correctCount} out of {activeQuiz.questions.length} correct.</p>
            <div className="flex justify-center gap-4">
              <button onClick={() => { setActiveQuiz(null); }} className="px-6 py-2 bg-white/10 text-white rounded-xl hover:bg-white/20 transition-colors">
                Back to Quizzes
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            {activeQuiz.questions.map((q: any, i: number) => {
              const isCorrect = answers[i] === q.correct_answer;
              return (
                <div key={i} className={`bg-white/5 border rounded-2xl p-6 ${isCorrect ? 'border-emerald-500/30' : 'border-rose-500/30'}`}>
                  <div className="flex items-start gap-3 mb-4">
                    {isCorrect ? <CheckCircle2 className="text-emerald-400 shrink-0 mt-1" /> : <XCircle className="text-rose-400 shrink-0 mt-1" />}
                    <h3 className="text-white font-medium">{q.question_text}</h3>
                  </div>
                  <div className="pl-9 space-y-2 text-sm">
                    <p className="text-slate-400">Your answer: <span className={isCorrect ? 'text-emerald-400' : 'text-rose-400'}>{answers[i] || 'None'}</span></p>
                    {!isCorrect && <p className="text-slate-400">Correct answer: <span className="text-emerald-400">{q.correct_answer}</span></p>}
                    <div className="mt-4 p-3 bg-white/5 rounded-lg text-slate-300">
                      <strong>Explanation:</strong> {q.explanation}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    const q = activeQuiz.questions[currentQIndex];
    return (
      <div className="max-w-2xl mx-auto bg-white/5 border border-white/10 rounded-2xl p-8">
        <div className="flex justify-between items-center mb-8 text-sm text-slate-400">
          <span>Question {currentQIndex + 1} of {activeQuiz.questions.length}</span>
          <span>{activeQuiz.title}</span>
        </div>
        
        <div className="w-full bg-white/10 h-2 rounded-full mb-8 overflow-hidden">
          <div className="bg-indigo-500 h-full transition-all" style={{ width: `${((currentQIndex + 1) / activeQuiz.questions.length) * 100}%` }} />
        </div>

        <h3 className="text-xl text-white font-medium mb-6">{q.question_text}</h3>
        
        <div className="space-y-3 mb-8">
          {q.options.map((opt: string, i: number) => (
            <label key={i} className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
              answers[currentQIndex] === opt 
                ? 'bg-indigo-500/20 border-indigo-500/50 text-white' 
                : 'border-white/10 text-slate-300 hover:bg-white/5'
            }`}>
              <input 
                type="radio" 
                name="q" 
                value={opt} 
                checked={answers[currentQIndex] === opt}
                onChange={() => setAnswers(prev => ({...prev, [currentQIndex]: opt}))}
                className="hidden"
              />
              <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                answers[currentQIndex] === opt ? 'border-indigo-400' : 'border-slate-500'
              }`}>
                {answers[currentQIndex] === opt && <div className="w-2.5 h-2.5 rounded-full bg-indigo-400" />}
              </div>
              {opt}
            </label>
          ))}
        </div>

        <div className="flex justify-between">
          <button 
            onClick={() => setCurrentQIndex(i => Math.max(0, i - 1))}
            disabled={currentQIndex === 0}
            className="px-4 py-2 flex items-center gap-2 text-slate-400 hover:text-white disabled:opacity-50"
          >
            <ArrowLeft size={16} /> Previous
          </button>
          {currentQIndex === activeQuiz.questions.length - 1 ? (
            <button 
              onClick={() => setSubmitted(true)}
              disabled={!answers[currentQIndex]}
              className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl font-medium hover:opacity-90 disabled:opacity-50"
            >
              Submit Quiz
            </button>
          ) : (
            <button 
              onClick={() => setCurrentQIndex(i => i + 1)}
              className="px-6 py-2 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-500 flex items-center gap-2"
            >
              Next <ArrowRight size={16} />
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Generate Panel */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 h-fit">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400">
            <Brain size={20} />
          </div>
          <h2 className="text-xl font-bold text-white">Generate Quiz</h2>
        </div>
        
        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Document</label>
            <select required value={genDocId} onChange={e => setGenDocId(e.target.value)} className="w-full bg-[#111113] border border-white/10 rounded-xl px-4 py-2.5 text-white focus:border-purple-500 outline-none">
              <option value="">Select a document...</option>
              {docs.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Difficulty</label>
            <select value={genDiff} onChange={e => setGenDiff(e.target.value)} className="w-full bg-[#111113] border border-white/10 rounded-xl px-4 py-2.5 text-white focus:border-purple-500 outline-none">
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Questions ({genNum})</label>
            <input type="range" min="1" max="20" value={genNum} onChange={e => setGenNum(parseInt(e.target.value))} className="w-full accent-purple-500" />
          </div>
          <button type="submit" disabled={generating || !genDocId} className="w-full py-3 mt-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-medium hover:opacity-90 disabled:opacity-50 flex justify-center items-center gap-2">
            {generating ? <Loader2 size={18} className="animate-spin" /> : 'Generate Now'}
          </button>
        </form>
      </div>

      {/* Quizzes List */}
      <div className="lg:col-span-2 space-y-4">
        <h2 className="text-xl font-bold text-white mb-6">My Quizzes</h2>
        {quizzes.length === 0 ? (
          <p className="text-slate-400">No quizzes generated yet.</p>
        ) : (
          quizzes.map(q => (
            <div key={q.id} className="bg-white/5 border border-white/10 rounded-xl p-5 flex items-center justify-between hover:bg-white/[0.07] transition-colors">
              <div>
                <h3 className="text-white font-medium text-lg">{q.title}</h3>
                <p className="text-slate-500 text-sm mt-1">{new Date(q.created_at).toLocaleDateString()}</p>
              </div>
              <button onClick={() => startQuiz(q.id)} className="px-4 py-2 bg-indigo-500/20 text-indigo-300 rounded-lg hover:bg-indigo-500/30 flex items-center gap-2 text-sm font-medium transition-colors">
                <Play size={16} /> Take Quiz
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
