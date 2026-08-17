import React, { useState, useEffect } from 'react';
import { apiGet, apiPost } from '../lib/api';
import { Brain, Play, CheckCircle2, XCircle, ArrowRight, ArrowLeft, Loader2, BookOpen } from 'lucide-react';

interface Quiz {
  id: string;
  title: string;
  document_id: string;
  created_at: string;
}

export default function Quizzes() {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [docs, setDocs] = useState<{id: string, title: string}[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  
  const [genDocId, setGenDocId] = useState('');
  const [genDiff, setGenDiff] = useState('medium');
  const [genNum, setGenNum] = useState(5);
  const [genType, setGenType] = useState('mcq');
  const [generating, setGenerating] = useState(false);

  const [activeQuiz, setActiveQuiz] = useState<any>(null);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [resultsData, setResultsData] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchQuizzes();
    apiGet<any[]>('/documents/').then(res => setDocs(res.filter(d => d.status === 'READY')));
  }, []);

  const fetchQuizzes = () => {
    apiGet<Quiz[]>('/knowledge/quizzes/').then(setQuizzes).catch(console.error);
    apiGet<any>('/knowledge/analytics/').then(res => setHistory(res.progression || [])).catch(console.error);
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const res = await apiPost<any>('/knowledge/quizzes/generate/', {
        document_id: genDocId,
        difficulty: genDiff,
        num_questions: genNum,
        question_type: genType,
      });
      fetchQuizzes();
      startQuiz(res.id);
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
      setResultsData(null);
    } catch (e) {
      console.error(e);
    }
  };

  const viewAttempt = async (attemptId: string) => {
    if (!attemptId) return;
    try {
      const res = await apiGet<any>(`/knowledge/quizzes/attempts/${attemptId}/`);
      setResultsData(res);
      setActiveQuiz({ id: res.quiz_id, title: "Quiz Result", questions: [] });
      setSubmitted(true);
    } catch (e) {
      console.error(e);
    }
  };

  const submitQuiz = async () => {
    if (!activeQuiz) return;
    setSubmitting(true);
    
    // Prepare answers payload
    const answersPayload = Object.entries(answers).map(([idx, ans]) => ({
      question_id: activeQuiz.questions[parseInt(idx)].id,
      answer: ans
    }));

    try {
      const res = await apiPost<any>(`/knowledge/quizzes/${activeQuiz.id}/submit/`, {
        answers: answersPayload
      });
      setResultsData(res);
      setSubmitted(true);
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  if (activeQuiz) {
    if (submitted && resultsData) {
      const score = resultsData.score_percentage;

      return (
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="minimal-card p-8 text-center">
            <h2 className="text-2xl font-semibold text-white mb-2">Quiz Complete</h2>
            <div className="text-6xl font-semibold text-white mb-6">
              {score}%
            </div>
            <p className="text-[#A1A1AA] mb-8">You got {resultsData.score} out of {resultsData.total} correct.</p>
            <div className="flex justify-center gap-4">
              <button onClick={() => { setActiveQuiz(null); }} className="minimal-button-secondary px-6 py-2">
                Back to Quizzes
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            {resultsData.results.map((res: any, i: number) => {
              const isCorrect = res.is_correct;
              return (
                <div key={i} className={`minimal-card p-6 border-l-4 ${isCorrect ? 'border-l-emerald-500' : 'border-l-red-500'}`}>
                  <div className="flex items-start gap-3 mb-4">
                    {isCorrect ? <CheckCircle2 className="text-emerald-500 shrink-0 mt-0.5" size={18} /> : <XCircle className="text-red-500 shrink-0 mt-0.5" size={18} />}
                    <h3 className="text-white font-medium">
                      {res.question_text || activeQuiz?.questions?.find((q: any) => q.id === res.question_id)?.text || "Question"}
                    </h3>
                  </div>
                  <div className="pl-8 space-y-2 text-sm">
                    <p className="text-[#A1A1AA]">Your answer: <span className={isCorrect ? 'text-emerald-400' : 'text-red-400'}>{res.user_answer || 'None'}</span></p>
                    {!isCorrect && <p className="text-[#A1A1AA]">Expected: <span className="text-emerald-400">{res.correct_answer}</span></p>}
                    
                    {(res.feedback || res.explanation) && (
                      <div className="mt-4 p-3 bg-[#111] rounded text-[#EDEDED]">
                        <strong>Feedback:</strong> {res.feedback || res.explanation}
                      </div>
                    )}

                    {res.source && (
                      <div className="mt-2 text-xs text-[#52525B] flex items-center gap-1">
                        <BookOpen size={12} /> Source: Page {res.source.page_number || '?'} 
                      </div>
                    )}
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
      <div className="max-w-2xl mx-auto minimal-card p-8">
        <div className="flex justify-between items-center mb-8 text-sm text-[#A1A1AA]">
          <span>Question {currentQIndex + 1} of {activeQuiz.questions.length}</span>
          <span className="font-medium text-white">{activeQuiz.title}</span>
        </div>
        
        <div className="w-full bg-[#111] h-1 rounded-full mb-8 overflow-hidden">
          <div className="bg-white h-full transition-all" style={{ width: `${((currentQIndex + 1) / activeQuiz.questions.length) * 100}%` }} />
        </div>

        <div className="mb-6">
          <span className="inline-block px-2 py-1 mb-3 text-xs font-medium text-black bg-white rounded uppercase tracking-wider">
            {q.question_type === 'open' ? 'Open Question' : q.question_type === 'true_false' ? 'True / False' : 'Multiple Choice'}
          </span>
          <h3 className="text-xl text-white font-medium leading-relaxed">{q.text || q.question_text}</h3>
        </div>
        
        <div className="space-y-3 mb-8">
          {q.question_type === 'open' ? (
            <textarea
              className="w-full minimal-input resize-none min-h-[120px]"
              placeholder="Type your answer here..."
              value={answers[currentQIndex] || ''}
              onChange={(e) => setAnswers(prev => ({...prev, [currentQIndex]: e.target.value}))}
            />
          ) : (
            (q.options || []).map((opt: string, i: number) => (
              <label key={i} className={`flex items-center gap-4 p-4 rounded border cursor-pointer transition-colors ${
                answers[currentQIndex] === opt 
                  ? 'bg-white text-black border-white' 
                  : 'border-[#333] text-[#EDEDED] hover:bg-[#111]'
              }`}>
                <input 
                  type="radio" 
                  name="q" 
                  value={opt} 
                  checked={answers[currentQIndex] === opt}
                  onChange={() => setAnswers(prev => ({...prev, [currentQIndex]: opt}))}
                  className="hidden"
                />
                <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                  answers[currentQIndex] === opt ? 'border-black' : 'border-[#666]'
                }`}>
                  {answers[currentQIndex] === opt && <div className="w-2 h-2 rounded-full bg-black" />}
                </div>
                {opt}
              </label>
            ))
          )}
        </div>

        <div className="flex justify-between items-center pt-4 border-t border-[#222]">
          <button 
            onClick={() => setCurrentQIndex(i => Math.max(0, i - 1))}
            disabled={currentQIndex === 0 || submitting}
            className="px-4 py-2 flex items-center gap-2 text-[#A1A1AA] hover:text-white disabled:opacity-50 text-sm font-medium transition-colors"
          >
            <ArrowLeft size={16} /> Previous
          </button>
          
          {currentQIndex === activeQuiz.questions.length - 1 ? (
            <button 
              onClick={submitQuiz}
              disabled={!answers[currentQIndex] || submitting}
              className="minimal-button-primary px-6 py-2"
            >
              {submitting ? <Loader2 size={16} className="animate-spin" /> : 'Submit Quiz'}
            </button>
          ) : (
            <button 
              onClick={() => setCurrentQIndex(i => i + 1)}
              className="minimal-button-secondary px-6 py-2 flex items-center gap-2"
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
      <div className="minimal-card p-6 h-fit">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded bg-[#111] border border-[#222] flex items-center justify-center text-white">
            <Brain size={16} />
          </div>
          <h2 className="text-xl font-semibold text-white">Generate Quiz</h2>
        </div>
        
        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-sm text-[#EDEDED] mb-1.5 font-medium">Document</label>
            <select required value={genDocId} onChange={e => setGenDocId(e.target.value)} className="w-full minimal-input">
              <option value="">Select a document...</option>
              {docs.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-[#EDEDED] mb-1.5 font-medium">Difficulty</label>
            <select value={genDiff} onChange={e => setGenDiff(e.target.value)} className="w-full minimal-input">
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-[#EDEDED] mb-1.5 font-medium">Type</label>
            <select value={genType} onChange={e => setGenType(e.target.value)} className="w-full minimal-input">
              <option value="mcq">Multiple Choice</option>
              <option value="true_false">True / False</option>
              <option value="open">Open Question</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-[#EDEDED] mb-1.5 font-medium">Questions ({genNum})</label>
            <input type="range" min="1" max="20" value={genNum} onChange={e => setGenNum(parseInt(e.target.value))} className="w-full accent-white" />
          </div>
          <button type="submit" disabled={generating || !genDocId} className="w-full minimal-button-primary py-2.5 mt-2 flex justify-center items-center gap-2">
            {generating ? <Loader2 size={18} className="animate-spin" /> : 'Generate Now'}
          </button>
        </form>
      </div>

      <div className="lg:col-span-2 space-y-4">
        <h2 className="text-xl font-semibold text-white mb-6">My Quizzes</h2>
        {quizzes.length === 0 ? (
          <p className="text-[#A1A1AA] text-sm">No quizzes generated yet.</p>
        ) : (
          quizzes.map(q => (
            <div key={q.id} className="minimal-card p-5 flex items-center justify-between hover:border-[#444] transition-colors">
              <div>
                <h3 className="text-white font-medium text-lg">{q.title}</h3>
                <p className="text-[#A1A1AA] text-sm mt-1">{new Date(q.created_at).toLocaleDateString()}</p>
              </div>
              <button onClick={() => startQuiz(q.id)} className="minimal-button-secondary px-4 py-2 flex items-center gap-2 text-sm">
                <Play size={14} /> Take Quiz
              </button>
            </div>
          ))
        )}
        <h2 className="text-xl font-semibold text-white mb-6 mt-10">Recent Results</h2>
        {history.length === 0 ? (
          <p className="text-[#A1A1AA] text-sm">No quiz attempts yet.</p>
        ) : (
          history.map((h, i) => (
            <div key={i} className="minimal-card p-5 flex items-center justify-between mb-4 hover:border-[#444] transition-colors">
              <div>
                <h3 className="text-white font-medium">{h.quiz_title}</h3>
                <p className="text-[#A1A1AA] text-sm mt-1">{h.date}</p>
              </div>
              <div className="flex items-center gap-4">
                <span className={`font-semibold text-lg ${h.score_percentage >= 70 ? 'text-emerald-400' : h.score_percentage >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                  {h.score_percentage}%
                </span>
                {h.id && (
                  <button onClick={() => viewAttempt(h.id)} className="text-sm text-[#A1A1AA] hover:text-white underline underline-offset-4">
                    View
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
