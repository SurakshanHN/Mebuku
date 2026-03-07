import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Camera, Mic, Layout, AlertCircle, Activity, ChevronRight, BarChart3, Users, Clock, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = `http://${window.location.hostname}:8001`;

// --- COMPONENT: Permission Modal ---
const PermissionModal = ({ onGrant }) => {
    const [status, setStatus] = useState({ mic: 'pending', cam: 'pending' });

    const requestAccess = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
            setStatus({ mic: 'granted', cam: 'granted' });
            // Stop the test stream immediately
            stream.getTracks().forEach(track => track.stop());
            setTimeout(onGrant, 1000);
        } catch (e) {
            alert("Permission denied! Please enable Camera and Mic in your browser settings to continue.");
        }
    };

    return (
        <div className="glass" style={{ padding: '3rem', textAlign: 'center', maxWidth: '500px', margin: '10% auto' }}>
            <Shield size={64} color="#6366f1" style={{ marginBottom: '1rem' }} />
            <h2>Security Permissions</h2>
            <p style={{ opacity: 0.7, marginBottom: '2rem' }}>This assessment requires active monitoring of your Camera and Microphone to ensure integrity.</p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginBottom: '2rem' }}>
                <div style={{ color: status.cam === 'granted' ? '#10b981' : '#f8fafc' }}>
                    <Camera size={32} />
                    <p style={{ fontSize: '0.8rem' }}>Camera</p>
                </div>
                <div style={{ color: status.mic === 'granted' ? '#10b981' : '#f8fafc' }}>
                    <Mic size={32} />
                    <p style={{ fontSize: '0.8rem' }}>Microphone</p>
                </div>
            </div>

            <button className="btn" onClick={requestAccess}>Grant Access & Continue</button>
        </div>
    );
};

// --- COMPONENT: Candidate View ---
const CandidateView = () => {
    const [sessionId, setSessionId] = useState('');
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [state, setState] = useState('welcome'); // welcome, permissions, quiz, finished

    const questions = [
        "What is the difference between an Array and a Linked List?",
        "How does a Hash Map handle collisions?",
        "Explain the concept of Big O notation.",
        "What is a Deadlock in multithreading?",
        "Describe the 4 pillars of Object-Oriented Programming.",
        "What is the difference between JOIN and UNION in SQL?",
        "How does Prototypal Inheritance work in JavaScript?",
        "Explain the difference between Process and Thread.",
        "What is a RESTful API?",
        "Describe the CAP theorem in distributed systems."
    ];

    const startTest = async () => {
        try {
            const res = await axios.post(`${API_BASE}/session/start`, { candidate_id: 'web_candidate_demo' });
            setSessionId(res.data.session_id);
            setState('permissions');
        } catch (e) {
            alert("Backend connection failed! Ensure Laptop 1 is running the backend.");
        }
    };

    if (state === 'welcome') {
        return (
            <div className="container" style={{ textAlign: 'center', marginTop: '10%' }}>
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass" style={{ padding: '3rem' }}>
                    <Shield size={64} color="#6366f1" style={{ marginBottom: '1rem' }} />
                    <h1>Project JD: Technical Assessment</h1>
                    <p style={{ opacity: 0.7, marginBottom: '2rem' }}>You are about to start a monitored technical interview.</p>
                    <button className="btn" onClick={startTest}>Initialize Session</button>
                </motion.div>
            </div>
        );
    }

    if (state === 'permissions') {
        return <PermissionModal onGrant={() => setState('quiz')} />;
    }

    if (state === 'finished') {
        return (
            <div className="container" style={{ textAlign: 'center', marginTop: '10%' }}>
                <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass" style={{ padding: '3rem', border: '2px solid #10b981' }}>
                    <CheckCircle2 size={64} color="#10b981" style={{ marginBottom: '1rem' }} />
                    <h1>Assessment Complete</h1>
                    <p>Your responses and technical signals have been securely synced.</p>
                    <p style={{ opacity: 0.5 }}>Session ID: <code>{sessionId}</code></p>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="container">
            <div className="glass" style={{ padding: '2rem', minHeight: '450px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', opacity: 0.7 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Activity size={16} className="pulse" /> Live Session: <code>{sessionId}</code>
                    </span>
                    <span>Question {currentQuestion + 1} of 10</span>
                </div>

                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentQuestion}
                        initial={{ x: 20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: -20, opacity: 0 }}
                    >
                        <h2 style={{ fontSize: '2.5rem', marginBottom: '2rem', lineHeight: 1.2 }}>{questions[currentQuestion]}</h2>
                    </motion.div>
                </AnimatePresence>

                <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '2rem' }}>
                    <div style={{ display: 'flex', gap: '1.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10b981' }}>
                            <Camera size={18} /> <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>CAM ON</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10b981' }}>
                            <Mic size={18} /> <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>MIC ON</span>
                        </div>
                    </div>
                    <button
                        className="btn"
                        onClick={() => currentQuestion < 9 ? setCurrentQuestion(q => q + 1) : setState('finished')}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                        {currentQuestion === 9 ? 'Finish Assessment' : 'Next Question'} <ChevronRight size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
};

// --- COMPONENT: Interviewer Dashboard ---
const InterviewerDashboard = () => {
    const [activeSessions, setActiveSessions] = useState([]);
    const [selectedId, setSelectedId] = useState('');
    const [data, setData] = useState(null);
    const [events, setEvents] = useState([]);

    // Auto-Discovery: List all sessions
    const fetchSessions = async () => {
        try {
            const res = await axios.get(`${API_BASE}/sessions`);
            setActiveSessions(res.data.sessions);
        } catch (e) {
            console.error("Discovery error", e);
        }
    };

    const pollData = async () => {
        if (!selectedId) return;
        try {
            const scoreRes = await axios.get(`${API_BASE}/session/${selectedId}/score`);
            setData(scoreRes.data);

            const eventRes = await axios.get(`${API_BASE}/session/${selectedId}`);
            setEvents(eventRes.data.events.reverse().slice(0, 15));
        } catch (e) {
            console.error("Polling error", e);
        }
    };

    useEffect(() => {
        fetchSessions();
        const interval = setInterval(fetchSessions, 5000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const interval = setInterval(pollData, 2000);
        return () => clearInterval(interval);
    }, [selectedId]);

    return (
        <div className="container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1>Forensic Intelligence</h1>
                    <p style={{ opacity: 0.6 }}>Automated Real-time Signal Sync</p>
                </div>

                {/* Session Selector (Auto-Discovery) */}
                <div className="glass" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Users size={20} color="#6366f1" />
                    <select
                        value={selectedId}
                        onChange={e => setSelectedId(e.target.value)}
                        style={{ background: 'transparent', border: 'none', color: 'white', outline: 'none', cursor: 'pointer' }}
                    >
                        <option value="" style={{ color: 'black' }}>Select Active Session...</option>
                        {activeSessions.map(s => (
                            <option key={s.session_id} value={s.session_id} style={{ color: 'black' }}>
                                {s.candidate_id} ({s.session_id.slice(0, 8)})
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {!selectedId ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                    {activeSessions.map(s => (
                        <motion.div
                            whileHover={{ scale: 1.02 }}
                            className="glass"
                            style={{ padding: '1.5rem', cursor: 'pointer', border: '1px solid #6366f144' }}
                            onClick={() => setSelectedId(s.session_id)}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                                <Users size={24} color="#6366f1" />
                                <span className="tag" style={{ background: '#6366f122', color: '#6366f1' }}>Active</span>
                            </div>
                            <h3>{s.candidate_id}</h3>
                            <p style={{ fontSize: '0.8rem', opacity: 0.5 }}>ID: {s.session_id}</p>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', fontSize: '0.8rem', opacity: 0.7 }}>
                                <Clock size={14} /> Started: {new Date(s.start_time * 1000).toLocaleTimeString()}
                            </div>
                        </motion.div>
                    ))}
                    {activeSessions.length === 0 && (
                        <div className="glass" style={{ padding: '4rem', textAlign: 'center', gridColumn: '1 / -1', opacity: 0.5 }}>
                            <Activity size={48} style={{ marginBottom: '1rem' }} />
                            <p>No active sessions found. Waiting for a candidate to start...</p>
                        </div>
                    )}
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
                    {/* Risk Card */}
                    <div className="glass" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '2rem' }}>
                            <button onClick={() => setSelectedId('')} style={{ background: 'none', border: 'none', color: '#6366f1', cursor: 'pointer', fontSize: '0.8rem' }}>← Back to List</button>
                            <span style={{ fontSize: '0.8rem', opacity: 0.5 }}>{selectedId.slice(0, 8)}</span>
                        </div>

                        <h3>Cheating Confidence</h3>
                        <div
                            className="risk-gauge"
                            style={{
                                border: `8px solid ${data?.risk_probability > 0.65 ? '#ef4444' : '#6366f1'}`,
                                color: data?.risk_probability > 0.65 ? '#ef4444' : '#6366f1',
                                boxShadow: `0 0 40px ${data?.risk_probability > 0.65 ? '#ef444433' : '#6366f133'}`,
                                margin: '2rem 0'
                            }}
                        >
                            {data?.risk_percentage || '0%'}
                        </div>

                        <div style={{ padding: '1rem', borderRadius: '0.5rem', background: data?.status === 'high_risk' ? '#ef444422' : '#10b98122', color: data?.status === 'high_risk' ? '#ef4444' : '#10b981', width: '100%' }}>
                            <span style={{ fontWeight: 'bold' }}>{data?.status.toUpperCase()} PROFILED</span>
                        </div>

                        {/* Final Verdict logic can be expanded here */}
                    </div>

                    {/* Real-time Sync Hub */}
                    <div className="glass" style={{ padding: '2rem', maxHeight: '600px', display: 'flex', flexDirection: 'column' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <h3>Live Signal Sync</h3>
                            <div style={{ color: '#10b981', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                <div className="pulse" style={{ width: 8, height: 8, background: '#10b981', borderRadius: '50%' }}></div> Live JSON Stream
                            </div>
                        </div>

                        <div style={{ overflowY: 'auto' }}>
                            {events.map((e, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="signal-card glass"
                                    style={{ marginBottom: '0.75rem', padding: '0.8rem' }}
                                >
                                    <div>
                                        <span style={{ fontSize: '0.7rem', opacity: 0.4, marginRight: '1rem' }}>{new Date(e.timestamp * 1000).toLocaleTimeString()}</span>
                                        <strong style={{ textTransform: 'uppercase', color: '#6366f1', fontSize: '0.9rem' }}>{e.signal.replace('_', ' ')}</strong>
                                    </div>
                                    <span className="tag" style={{ background: e.value > 0.6 ? '#ef444422' : '#10b98122', color: e.value > 0.6 ? '#ef4444' : '#10b981' }}>
                                        {e.value.toFixed(2)}
                                    </span>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            <style dangerouslySetInnerHTML={{
                __html: `
        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.5; }
          100% { transform: scale(1); opacity: 1; }
        }
        .pulse { animation: pulse 2s infinite; }
      `}} />
        </div>
    );
};

// --- MAIN APP ---
function App() {
    const path = window.location.pathname;

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <nav className="glass" style={{ margin: '1rem 2rem', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', fontSize: '1.2rem' }}>
                    <Shield color="#6366f1" fill="#6366f122" /> PROJECT JD
                </div>
                <div style={{ display: 'flex', gap: '2rem' }}>
                    <a href="/test" style={{ color: 'white', textDecoration: path === '/test' ? 'underline' : 'none', fontWeight: 600 }}>CANDIDATE TEST</a>
                    <a href="/dashboard" style={{ color: 'white', textDecoration: path === '/dashboard' ? 'underline' : 'none', fontWeight: 600 }}>INTERVIEWER DASHBOARD</a>
                </div>
            </nav>

            <main style={{ flex: 1 }}>
                {path === '/dashboard' ? <InterviewerDashboard /> : <CandidateView />}
            </main>

            <footer style={{ padding: '2rem', textAlign: 'center', opacity: 0.3, fontSize: '0.8rem' }}>
                © 2026 Project JD Forensic Engine | Confidential
            </footer>
        </div>
    );
}

export default App;
