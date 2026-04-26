import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AdminContext } from '../context/AdminContext';
import { PortfolioContext } from '../context/PortfolioContext';
import { motion, AnimatePresence } from 'framer-motion';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

import MessageInbox from '../components/MessageInbox';
import CollectionEditor from '../components/CollectionEditor';
import { Layout, FileText, BarChart3, ListTree, Settings as SettingsIcon, ShieldCheck, X } from 'lucide-react';

const Admin = () => {
    const { isAuthenticated, login, logout, token } = useContext(AdminContext);
    const { data, fetchPortfolio, updatePortfolio } = useContext(PortfolioContext);
    const navigate = useNavigate();

    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [command, setCommand] = useState('');
    const [cmdResult, setCmdResult] = useState(null);
    const [activeTab, setActiveTab] = useState('dashboard');
    const [editingItem, setEditingItem] = useState(null); // { type, item }

    // Local state for edits
    const [formData, setFormData] = useState(null);
    const [resumeFile, setResumeFile] = useState(null);
    const [allProjects, setAllProjects] = useState([]);
    const [toastMessage, setToastMessage] = useState(null);

    const showToast = (text, type = 'success') => {
        setToastMessage({ text, type });
        setTimeout(() => setToastMessage(null), 3000);
    };

    useEffect(() => {
        if (data) {
            const copy = JSON.parse(JSON.stringify(data));
            if (!copy.profile) copy.profile = {};
            if (!copy.profile.personal) copy.profile.personal = {};
            copy.profile.personal.gender = 'Female';
            copy.profile.personal.military_service = 'No';
            setFormData(copy);
        }
    }, [data]);

    useEffect(() => {
        if (isAuthenticated) {
            fetch('http://localhost:8000/api/admin/projects/all/')
                .then(res => {
                    if (!res.ok) throw new Error('Failed to fetch projects');
                    return res.json();
                })
                .then(data => setAllProjects(data))
                .catch(err => {
                    console.error(err);
                    setAllProjects([]); // Fallback to empty
                });
        }
    }, [isAuthenticated]);

    const handleLogin = async (e) => {
        e.preventDefault();
        const success = await login(password);
        if (!success) setError('Invalid password');
    };

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const saveChanges = async () => {
        const success = await updatePortfolio(formData);
        if (success) {
            showToast('Artifacts Deposited Successfully', 'success');
            // Refresh to ensure we have the latest server state (including IDs)
            await fetchPortfolio();
        } else {
            showToast('Failed to deposit artifacts. Check backend logs.', 'error');
        }
    };

    const handleChange = (section, field, value) => {
        setFormData(prev => ({
            ...prev,
            [section]: { ...prev[section], [field]: value }
        }));
    };

    const handleAboutChange = (idx, value) => {
        const newAbout = [...formData.about];
        newAbout[idx] = value;
        setFormData(prev => ({ ...prev, about: newAbout }));
    };

    const handleSkillsChange = (val) => {
        const newSkills = val.split(',').map(s => s.trim()).filter(s => s);
        setFormData(prev => ({ ...prev, skills: newSkills }));
    };

    const handleCommand = async (e) => {
        e.preventDefault();
        setCmdResult('Processing...');
        try {
            const res = await fetch('http://localhost:8000/api/admin/command/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command })
            });
            const resData = await res.json();
            setCmdResult(JSON.stringify(resData.changes_applied, null, 2));
            await fetchPortfolio(); // refresh to show changes
        } catch (err) {
            setCmdResult('Error executing command');
        }
    };

    const handleAIAction = async (endpoint, payload, callback) => {
        try {
            const res = await fetch(`http://localhost:8000/api/admin/${endpoint}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            const result = data.rewritten || data.summary || data.bio || data.bullets;
            if (result) {
                callback(result);
                showToast('AI Synthesis Complete', 'success');
            }
            else throw new Error("No result found");
        } catch (err) {
            showToast('AI Action failed: ' + err.message, 'error');
        }
    };


    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-ivory flex flex-col items-center justify-center relative z-20">
                <form onSubmit={handleLogin} className="bg-white p-12 border border-warmBrown/5 shadow-2xl flex flex-col gap-8 max-w-sm w-full">
                    <div className="text-center">
                        <h2 className="text-4xl font-serif italic mb-2">Vault Entry</h2>
                        <p className="font-mono text-[10px] uppercase tracking-widest text-warmBrown/40">Secure Signal Required</p>
                    </div>
                    {error && <p className="text-red-500 text-[10px] text-center font-mono uppercase tracking-tighter">{error}</p>}
                    <input
                        type="password"
                        placeholder="DIGITAL KEY"
                        className="border-b border-warmBrown/10 p-3 focus:outline-none focus:border-accent font-mono text-center text-sm placeholder:opacity-20 transition-colors"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <button type="submit" className="bg-warmBrown text-ivory py-4 font-mono text-xs tracking-[0.4em] uppercase hover:bg-black transition-all">
                        Decrypt
                    </button>
                </form>
            </div>
        );
    }
    if (!formData) return <div className="min-h-screen bg-ivory flex items-center justify-center font-mono text-[10px] text-warmBrown/40 italic">Synchronizing State...</div>;

    const tabs = [
        { id: 'dashboard', label: 'Monitor', icon: <BarChart3 size={14} /> },
        { id: 'content', label: 'Identity', icon: <FileText size={14} /> },
        { id: 'collections', label: 'Artifacts', icon: <ListTree size={14} /> },
        { id: 'settings', label: 'Core', icon: <SettingsIcon size={14} /> }
    ];

    return (
        <div className="min-h-screen bg-ivory pt-8 pb-24 px-6 relative z-20">
            {/* Toast Notification */}
            <AnimatePresence>
                {toastMessage && (
                    <motion.div
                        initial={{ opacity: 0, y: -50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -50 }}
                        className={`fixed top-8 left-1/2 -translate-x-1/2 px-6 py-4 font-mono text-[10px] uppercase tracking-widest z-[200] shadow-2xl border flex items-center gap-3 ${
                            toastMessage.type === 'error' 
                            ? 'bg-red-50 text-red-600 border-red-200' 
                            : 'bg-warmBlack text-accent border-accent/20'
                        }`}
                    >
                        <ShieldCheck size={14} />
                        {toastMessage.text}
                    </motion.div>
                )}
            </AnimatePresence>
            <div className="max-w-6xl mx-auto">

                {/* Superior Header */}
                <div className="flex flex-col md:flex-row justify-between items-center bg-white border border-warmBrown/5 p-8 shadow-sm mb-12">
                    <div className="flex items-center gap-4 mb-4 md:mb-0">
                        <div className="w-12 h-12 bg-warmBlack text-ivory flex items-center justify-center">
                            <ShieldCheck size={24} />
                        </div>
                        <div>
                            <h1 className="text-3xl font-serif italic text-warmBrown leading-none">Command Center</h1>
                            <p className="font-mono text-[10px] uppercase tracking-widest text-warmBrown/30 mt-1">Authorized Access Only // Port 8001</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex bg-ivory p-1">
                            {tabs.map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-6 py-2 font-mono text-[10px] uppercase tracking-widest transition-all ${activeTab === tab.id ? 'bg-white text-accent shadow-sm' : 'text-warmBrown/40 hover:text-warmBrown'}`}
                                >
                                    {tab.icon}
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                        <button onClick={handleLogout} className="ml-4 w-10 h-10 flex items-center justify-center border border-warmBrown/10 text-warmBrown/20 hover:text-red-500 hover:border-red-500/20 transition-all" title="Terminate Session">
                            <ShieldCheck size={16} />
                        </button>
                    </div>
                </div>

                {/* Tab Content Rendering */}
                <div className="space-y-12 min-h-[600px]">
                    {activeTab === 'dashboard' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <AnalyticsDashboard />
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                                <MessageInbox />
                            </div>
                        </div>
                    )}

                    {activeTab === 'content' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            {/* Profile Editor */}
                            <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                <h3 className="font-serif text-xl border-b border-warmBrown/5 pb-4 italic">Identity Matrix</h3>
                                {['name', 'role', 'email', 'phone', 'location', 'summary', 'bio'].map(field => (
                                    <div key={field}>
                                        <label className="block text-[9px] font-mono text-warmBrown/40 mb-1 uppercase tracking-widest">{field}</label>
                                        {field === 'summary' || field === 'bio' ? (
                                            <textarea
                                                className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif bg-transparent resize-none h-20"
                                                value={formData.profile[field] || ''}
                                                onChange={e => handleChange('profile', field, e.target.value)}
                                            />
                                        ) : (
                                            <input
                                                className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif bg-transparent"
                                                value={formData.profile[field] || ''}
                                                onChange={e => handleChange('profile', field, e.target.value)}
                                            />
                                        )}
                                    </div>
                                ))}

                                <div className="pt-4 border-t border-warmBrown/5 space-y-4">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold">Connections & Socials</h4>
                                        <span className="font-mono text-[8px] text-warmBrown/20 uppercase tracking-[0.2em]">{formData.connections?.length || 0} signals</span>
                                    </div>
                                    <CollectionEditor
                                        type="connections"
                                        items={formData.connections || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, connections: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'connections', item })}
                                    />
                                </div>

                                <div className="pt-4 border-t border-warmBrown/5 space-y-4">
                                    <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold">Regional Metadata (Personal)</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        {[
                                            { key: 'dob', label: 'Date of Birth', type: 'date' },
                                            { key: 'gender', label: 'Gender', type: 'static', value: 'Female' },
                                            { key: 'nationality', label: 'Nationality', type: 'text' },
                                            { key: 'marital_status', label: 'Marital Status', type: 'select', options: ['Single', 'Married', 'Divorced'] },
                                            { key: 'visa_status', label: 'Visa Status', type: 'text' },
                                            { key: 'military_service', label: 'Military Service', type: 'static', value: 'No' },
                                            { key: 'wechat_id', label: 'WeChat ID', type: 'text' },
                                            { key: 'kakaotalk_id', label: 'KakaoTalk ID', type: 'text' },
                                            { key: 'political_status', label: 'Political Status', type: 'text' },
                                            { key: 'korean_language_level', label: 'Korean Language Level', type: 'text' }
                                        ].map(field => (
                                            <div key={field.key}>
                                                <label className="block text-[9px] font-mono text-warmBrown/40 mb-1 uppercase tracking-widest">{field.label}</label>
                                                {field.type === 'static' ? (
                                                    <input
                                                        className="w-full border-b border-warmBrown/10 py-2 font-sans text-xs bg-transparent text-warmBrown/50 cursor-not-allowed"
                                                        value={field.value}
                                                        disabled
                                                    />
                                                ) : field.type === 'select' ? (
                                                    <select
                                                        className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-sans text-xs bg-transparent"
                                                        value={formData.profile?.personal?.[field.key] || ''}
                                                        onChange={e => {
                                                            const personal = formData.profile.personal || {};
                                                            handleChange('profile', 'personal', { ...personal, [field.key]: e.target.value });
                                                        }}
                                                    >
                                                        <option value="">Select {field.label}</option>
                                                        {field.options.map(opt => (
                                                            <option key={opt} value={opt}>{opt}</option>
                                                        ))}
                                                    </select>
                                                ) : (
                                                    <input
                                                        type={field.type}
                                                        className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-sans text-xs bg-transparent"
                                                        value={formData.profile?.personal?.[field.key] || ''}
                                                        placeholder={`Enter ${field.label}`}
                                                        onChange={e => {
                                                            const personal = formData.profile.personal || {};
                                                            handleChange('profile', 'personal', { ...personal, [field.key]: e.target.value });
                                                        }}
                                                    />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                    <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold mt-4">Regional Metadata (Visa Info)</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        {['visaType', 'visaIssueDate', 'visaExpiryDate'].map(field => (
                                            <div key={field}>
                                                <label className="block text-[9px] font-mono text-warmBrown/40 mb-1 uppercase tracking-widest">{field.replace(/([A-Z])/g, ' $1').trim()}</label>
                                                <input
                                                    className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-sans text-xs bg-transparent"
                                                    value={formData.profile?.visa_info?.[field] || ''}
                                                    placeholder={`Enter ${field}`}
                                                    onChange={e => {
                                                        const visa_info = formData.profile.visa_info || {};
                                                        handleChange('profile', 'visa_info', { ...visa_info, [field]: e.target.value });
                                                    }}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                    <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold mt-4">Japan Metadata (Personal)</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        {[
                                            { key: 'name_furigana', label: 'ふりがな (Name Reading)', placeholder: 'ディヴィア・ニランカリ' },
                                            { key: 'nationality_ja', label: '国籍 (Nationality in Japanese)', placeholder: 'インド' },
                                            { key: 'address_furigana', label: '住所ふりがな (Address Reading)', placeholder: 'インド グジャラート州 スーラト' },
                                            { key: 'commute_time', label: '通勤時間 (Commute Time)', placeholder: '約1時間' },
                                            { key: 'dependents_count', label: '扶養家族数 (Number of Dependents)', type: 'number', placeholder: '0' },
                                            { key: 'has_spouse', label: '配偶者 (Spouse)', type: 'boolean' },
                                            { key: 'spouse_dependency', label: '配偶者の扶養義務 (Spouse Dependency)', type: 'boolean' },
                                            { key: 'self_pr_ja', label: '自己PR 履歴書用 (Self PR for Rirekisho)', type: 'textarea' },
                                            { key: 'self_pr_ja_detailed', label: '自己PR 職務経歴書用 (Self PR for Shokumu)', type: 'textarea' },
                                            { key: 'career_summary_ja', label: '職務要約 (Career Summary)', type: 'textarea' },
                                            { key: 'desired_conditions_ja', label: '本人希望 (Desired Conditions)', placeholder: '貴社の規定に従います。' },
                                        ].map(field => (
                                            <div key={field.key} className={field.type === 'textarea' ? "col-span-2" : ""}>
                                                <label className="block text-[9px] font-mono text-warmBrown/40 mb-1 uppercase tracking-widest">{field.label}</label>
                                                {field.type === 'textarea' ? (
                                                    <textarea
                                                        className="w-full border border-warmBrown/10 p-3 focus:outline-none focus:border-accent font-sans text-xs bg-transparent min-h-[80px]"
                                                        value={formData.profile?.personal?.[field.key] || ''}
                                                        placeholder={field.placeholder || `Enter ${field.label}`}
                                                        onChange={e => {
                                                            const personal = formData.profile.personal || {};
                                                            handleChange('profile', 'personal', { ...personal, [field.key]: e.target.value });
                                                        }}
                                                    />
                                                ) : field.type === 'boolean' ? (
                                                    <select
                                                        className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-sans text-xs bg-transparent"
                                                        value={formData.profile?.personal?.[field.key] ? 'true' : 'false'}
                                                        onChange={e => {
                                                            const personal = formData.profile.personal || {};
                                                            handleChange('profile', 'personal', { ...personal, [field.key]: e.target.value === 'true' });
                                                        }}
                                                    >
                                                        <option value="false">No / False</option>
                                                        <option value="true">Yes / True</option>
                                                    </select>
                                                ) : (
                                                    <input
                                                        type={field.type === 'number' ? 'number' : 'text'}
                                                        className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-sans text-xs bg-transparent"
                                                        value={formData.profile?.personal?.[field.key] || ''}
                                                        placeholder={field.placeholder || `Enter ${field.label}`}
                                                        onChange={e => {
                                                            const personal = formData.profile.personal || {};
                                                            let val = e.target.value;
                                                            if (field.type === 'number') val = val ? parseInt(val, 10) : 0;
                                                            handleChange('profile', 'personal', { ...personal, [field.key]: val });
                                                        }}
                                                    />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-warmBrown/5 space-y-4">
                                    <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold">Professional Photo</h4>
                                    <div className="flex items-center gap-6 bg-ivory/20 p-4 border border-warmBrown/5">
                                        <div className="w-20 h-24 bg-white border border-warmBrown/10 overflow-hidden flex items-center justify-center">
                                            {formData.profile.photo ? (
                                                <img src={`http://localhost:8000/${formData.profile.photo}?t=${Date.now()}`} alt="Profile" className="w-full h-full object-cover" />
                                            ) : (
                                                <span className="text-[8px] font-mono text-warmBrown/20 uppercase text-center p-2">No Photo Signal</span>
                                            )}
                                        </div>
                                        <div className="flex-1 space-y-2">
                                            <p className="text-[10px] font-sans text-warmBrown/60">Upload used for Korea, Japan, China, Germany, and Middle East resumes.</p>
                                            <input
                                                type="file"
                                                accept="image/*"
                                                className="hidden"
                                                id="photo-upload"
                                                onChange={async (e) => {
                                                    const file = e.target.files[0];
                                                    if (!file) return;
                                                    const uploadData = new FormData();
                                                    uploadData.append('file', file);
                                                    const res = await fetch('http://localhost:8000/api/admin/profile-photo/', {
                                                        method: 'POST',
                                                        body: uploadData
                                                    });
                                                    const resJson = await res.json();
                                                    if (resJson.url) {
                                                        handleChange('profile', 'photo', 'uploads/profile_photo.jpg');
                                                        showToast('Photo Decanted Successfully');
                                                    }
                                                }}
                                            />
                                            <label htmlFor="photo-upload" className="inline-block px-4 py-2 border border-warmBrown/20 font-mono text-[9px] uppercase tracking-widest cursor-pointer hover:bg-warmBrown hover:text-ivory transition-all">
                                                Upload New Signal
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-[9px] font-mono text-warmBrown/40 mb-2 uppercase tracking-widest flex justify-between">
                                        Professional Summary (For Resume)
                                        <button
                                            onClick={() => handleAIAction('rewrite-summary', { about_list: formData.about }, (newText) => handleChange('profile', 'summary', newText))}
                                            className="text-accent hover:underline lowercase italic"
                                        >✦ auto-gen from narrative</button>
                                    </label>
                                    <textarea
                                        className="w-full border border-warmBrown/10 p-3 focus:outline-none focus:border-accent font-sans text-xs h-20 bg-ivory/20"
                                        value={formData.profile.summary || ''}
                                        onChange={e => handleChange('profile', 'summary', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[9px] font-mono text-warmBrown/40 mb-2 uppercase tracking-widest">Typewriter Titles (Comma Separated)</label>
                                    <textarea
                                        className="w-full border border-warmBrown/10 p-3 focus:outline-none focus:border-accent font-mono text-[10px] h-20 bg-ivory/20"
                                        value={(formData.profile.titles || []).join(', ')}
                                        onChange={e => {
                                            const newTitles = e.target.value.split(',').map(t => t.trim()).filter(t => t);
                                            setFormData(prev => ({ ...prev, profile: { ...prev.profile, titles: newTitles } }));
                                        }}
                                    />
                                </div>
                                <button onClick={saveChanges} className="w-full py-4 bg-warmBrown text-ivory font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-black transition-all">Preserve Identity</button>
                            </div>

                            {/* About & Stats */}
                            <div className="space-y-8">
                                <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                    <h3 className="font-serif text-xl border-b border-warmBrown/5 pb-4 flex justify-between items-center italic">
                                        Narrative sequence
                                        <button
                                            onClick={() => handleAIAction('rewrite-about', { text: formData.about.join('\n') }, (newText) => setFormData(p => ({ ...p, about: newText.split('\n') })))}
                                            className="text-accent font-mono text-[9px] hover:underline uppercase tracking-widest"
                                        >✦ enrich sequence</button>
                                    </h3>
                                    {formData.about.map((para, idx) => (
                                        <textarea
                                            key={idx}
                                            className="w-full border border-warmBrown/10 p-3 focus:outline-none focus:border-accent font-sans text-sm h-24 bg-ivory/20 mb-2"
                                            value={para}
                                            onChange={e => handleAboutChange(idx, e.target.value)}
                                        />
                                    ))}
                                    <button onClick={saveChanges} className="w-full py-4 bg-warmBrown text-ivory font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-black transition-all">Commit Narrative</button>
                                </div>

                                <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                    <h3 className="font-serif text-xl border-b border-warmBrown/5 pb-4 italic">Metric Flux</h3>
                                    <div className="grid grid-cols-2 gap-6">
                                        {Object.keys(formData.stats || {}).map(stat => (
                                            <div key={stat}>
                                                <label className="block text-[9px] font-mono text-warmBrown/40 mb-1 uppercase tracking-widest truncate">{stat.replace('_', ' ')}</label>
                                                <input
                                                    className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-center text-accent"
                                                    value={formData.stats[stat]}
                                                    onChange={e => handleChange('stats', stat, e.target.value)}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                    <button onClick={saveChanges} className="w-full py-4 bg-accent text-ivory font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-warmBlack transition-all">Sync Metrics</button>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'collections' && (
                        <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                                {/* Experience */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Experience</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.experience?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="experience"
                                        items={formData.experience || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, experience: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'experience', item })}
                                    />
                                </div>

                                {/* Education */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Education</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.education?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="education"
                                        items={formData.education || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, education: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'education', item })}
                                    />
                                </div>

                                {/* Extracurriculars */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Extracurriculars / Languages</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.extracurriculars?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="extracurriculars"
                                        items={formData.extracurriculars || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, extracurriculars: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'extracurriculars', item })}
                                    />
                                </div>

                                {/* Certifications */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Certifications</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.certifications?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="certifications"
                                        items={formData.certifications || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, certifications: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'certifications', item })}
                                    />
                                </div>

                                {/* Achievements */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Achievements</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.achievements?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="achievements"
                                        items={formData.achievements || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, achievements: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'achievements', item })}
                                    />
                                </div>

                                {/* Projects */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <div className="flex items-center gap-4">
                                            <h3 className="font-serif text-2xl italic">Project Artifacts</h3>
                                            <button
                                                onClick={(e) => { e.preventDefault(); handleCommand(e, "Sync my latest projects from GitHub"); }}
                                                className="text-[9px] font-mono text-accent hover:border-b border-accent uppercase tracking-widest pt-1"
                                            >( Sync Pulse )</button>
                                        </div>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.projects?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="projects"
                                        items={formData.projects || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, projects: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'projects', item })}
                                    />

                                    {/* GitHub Sync List (Visibility Only) */}
                                    <div className="mt-8 bg-ivory/30 p-6 border border-warmBrown/5">
                                        <h4 className="font-serif text-sm italic mb-4 flex justify-between items-center">
                                            GitHub Repository Visibility
                                            <span className="font-mono text-[8px] uppercase tracking-widest opacity-30">Dynamic Source</span>
                                        </h4>
                                        <div className="space-y-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                                            {allProjects.map(repo => (
                                                <div key={repo.name} className="flex justify-between items-center bg-white p-3 border border-warmBrown/5">
                                                    <div className="flex flex-col">
                                                        <span className="font-serif text-xs">{repo.name}</span>
                                                        <span className="font-mono text-[8px] text-warmBrown/40 uppercase">{repo.language || 'Unknown Stack'}</span>
                                                    </div>
                                                    <button
                                                        onClick={() => {
                                                            const currentVisibility = formData.project_visibility || {};
                                                            const isVisible = currentVisibility[repo.name] !== false;
                                                            setFormData(prev => ({
                                                                ...prev,
                                                                project_visibility: {
                                                                    ...currentVisibility,
                                                                    [repo.name]: !isVisible
                                                                }
                                                            }));
                                                        }}
                                                        className={`font-mono text-[9px] uppercase tracking-tighter px-3 py-1 border transition-all ${formData.project_visibility?.[repo.name] !== false
                                                            ? 'border-accent/20 text-accent hover:bg-accent hover:text-white'
                                                            : 'border-warmBrown/10 text-warmBrown/30 hover:bg-warmBrown hover:text-ivory'
                                                            }`}
                                                    >
                                                        {formData.project_visibility?.[repo.name] !== false ? '[ VISIBLE ]' : '[ HIDDEN ]'}
                                                    </button>
                                                </div>
                                            ))}
                                            {allProjects.length === 0 && (
                                                <p className="text-center font-mono text-[10px] text-warmBrown/20 py-8 italic uppercase tracking-widest">Awaiting GitHub Signal...</p>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Testimonials */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Testimonials</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.testimonials?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="testimonials"
                                        items={formData.testimonials || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, testimonials: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'testimonials', item })}
                                    />
                                </div>

                                {/* Research */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Research Lab</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.researchInterests?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="research"
                                        items={formData.researchInterests || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, researchInterests: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'research', item })}
                                    />
                                </div>

                                {/* Languages */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Languages</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.languages?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="languages"
                                        items={formData.languages || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, languages: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'languages', item })}
                                    />
                                </div>

                                {/* Skill Categories */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Skill Framework</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.skillCategories?.length || 0} nodes</span>
                                    </div>
                                    <CollectionEditor
                                        type="skills"
                                        items={formData.skillCategories || []}
                                        setItems={(newItems) => setFormData(prev => ({ ...prev, skillCategories: newItems }))}
                                        onEdit={(item) => setEditingItem({ type: 'skills', item })}
                                    />
                                </div>

                                {/* Activity Signal (Read-Only) */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic">Signal History</h3>
                                        <span className="font-mono text-[9px] text-warmBrown/30 uppercase tracking-[0.2em]">{formData.activityLog?.length || 0} nodes</span>
                                    </div>
                                    <div className="flex flex-col gap-2 max-h-96 overflow-y-auto pr-2">
                                        {(formData.activityLog || []).slice(0, 100).map((act, i) => (
                                            <div key={i} className="flex justify-between items-center p-3 border border-warmBrown/5 bg-white">
                                                <div className="flex flex-col">
                                                    <span className="font-mono text-[10px] uppercase text-warmBrown">{act.action}</span>
                                                    <span className="font-mono text-[9px] uppercase tracking-widest text-warmBrown/40 mt-1">{act.description}</span>
                                                </div>
                                                <span className="font-mono text-[9px] text-warmBrown/30">{act.date}</span>
                                            </div>
                                        ))}
                                        {(!formData.activityLog || formData.activityLog.length === 0) && (
                                            <div className="py-8 text-center text-warmBrown/30 font-mono text-[10px] uppercase tracking-widest border border-dashed border-warmBrown/10">No signals detected</div>
                                        )}
                                    </div>
                                </div>

                                {/* Blog */}
                                <div className="space-y-6">
                                    <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                                        <h3 className="font-serif text-2xl italic text-center w-full">Thought Canvas</h3>
                                    </div>
                                    <CollectionEditor
                                        type="blog"
                                        items={formData.blogPosts || []}
                                        setItems={(newItems) => setFormData({ ...formData, blogPosts: newItems })}
                                        onEdit={(item) => setEditingItem({ type: 'blog', item })}
                                    />
                                </div>
                            </div>
                            <button onClick={saveChanges} className="fixed bottom-8 right-8 w-48 py-4 bg-accent text-white font-mono text-xs shadow-2xl z-50 hover:bg-warmBlack transition-all uppercase tracking-widest">Deposit Artifacts</button>
                        </div>
                    )}

                    {activeTab === 'settings' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-32">
                            <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-8">
                                <h3 className="font-serif text-xl border-b border-warmBrown/5 pb-4 italic">Visibility Map</h3>
                                <div className="flex flex-wrap gap-4">
                                    {Object.keys(formData.sections_visibility).map(sec => (
                                        <div key={sec} className="flex-auto min-w-[140px] flex items-center justify-between gap-4 bg-ivory/20 p-4 border border-warmBrown/5 hover:border-accent/10 transition-colors">
                                            <span className="font-mono text-sm lowercase text-warmBrown/70">{sec}</span>
                                            <button
                                                onClick={() => {
                                                    const newVal = !formData.sections_visibility[sec];
                                                    handleChange('sections_visibility', sec, newVal);
                                                }}
                                                className={`text-sm font-mono transition-all hover:scale-105 ${formData.sections_visibility[sec] ? 'text-accent' : 'text-warmBrown/30'}`}
                                            >
                                                {formData.sections_visibility[sec] ? '[Enabled]' : '[Disabled]'}
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-8">
                                <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                    <h3 className="font-serif text-xl border-b border-warmBrown/5 pb-4 italic">Core Presentation</h3>
                                    <div className="flex justify-between items-center bg-ivory/20 p-4 border border-warmBrown/5 hover:border-accent/20 transition-colors">
                                        <span className="font-mono text-[10px] uppercase tracking-widest text-warmBrown/60">3D Particle Hero (Canvas Effect)</span>
                                        <button
                                            onClick={() => {
                                                const newVal = formData.settings?.hero3d !== false ? false : true;
                                                setFormData(prev => ({
                                                    ...prev,
                                                    settings: {
                                                        ...(prev.settings || {}),
                                                        hero3d: newVal
                                                    }
                                                }));
                                            }}
                                            className={`px-3 py-1 text-[9px] font-mono tracking-tighter transition-colors ${formData.settings?.hero3d !== false ? 'text-accent font-bold' : 'text-warmBrown/20'}`}
                                        >
                                            {formData.settings?.hero3d !== false ? '[ ENABLED ]' : '[ DISABLED ]'}
                                        </button>
                                    </div>
                                </div>
                                <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                    <h3 className="font-serif text-xl border-b border-warmBrown/5 pb-4 italic">Resume Engine Settings</h3>
                                    <div>
                                        <label className="block text-[9px] font-mono text-warmBrown/40 mb-2 uppercase tracking-widest">Default Detection Fallback</label>
                                        <select
                                            className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px] bg-transparent uppercase tracking-widest"
                                            value={formData.resumeSettings?.defaultRegion || 'international'}
                                            onChange={e => setFormData(prev => ({
                                                ...prev,
                                                resumeSettings: { ...prev.resumeSettings, defaultRegion: e.target.value }
                                            }))}
                                        >
                                            <option value="international">International (ATS)</option>
                                            <option value="korea">South Korea</option>
                                            <option value="japan">Japan</option>
                                            <option value="china">China</option>
                                            <option value="germany">Germany</option>
                                            <option value="middleeast">Middle East</option>
                                        </select>
                                        <p className="mt-4 text-[9px] font-mono text-warmBrown/30 leading-relaxed uppercase tracking-widest border-l border-accent/20 pl-4 py-2 italic font-bold">
                                            Note: Photo is NEVER included in International/ATS format regardless of upload status.
                                        </p>
                                    </div>
                                </div>

                                <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                    <h3 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold">Terminal_AI</h3>
                                    <form onSubmit={handleCommand} className="flex gap-2">
                                        <input
                                            type="text"
                                            placeholder="Awaiting command sequence..."
                                            className="flex-1 border-b border-warmBrown/10 p-3 font-mono text-xs focus:outline-none focus:border-accent bg-transparent"
                                            value={command}
                                            onChange={(e) => setCommand(e.target.value)}
                                        />
                                        <button type="submit" className="bg-warmBlack text-ivory px-6 font-mono text-[10px] uppercase hover:bg-black">Run</button>
                                    </form>
                                    {cmdResult && (
                                        <pre className="mt-4 p-6 bg-warmBlack text-accent font-mono text-[10px] overflow-x-auto leading-relaxed border border-accent/20">
                                            {`> Execution Successful\n> Result Output:\n${cmdResult}`}
                                        </pre>
                                    )}
                                </div>
                            </div>

                            <div className="lg:col-span-2 bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                <div className="flex justify-between items-center border-b border-warmBrown/5 pb-4 mb-4">
                                    <h3 className="font-serif text-xl italic">
                                        Live Resume Preview
                                    </h3>
                                    <a href={`http://localhost:8000/api/resume/download/${formData.resumeSettings?.defaultRegion || 'international'}?download=true`} target="_blank" rel="noreferrer" className="px-6 py-3 bg-accent text-white font-mono text-[10px] uppercase tracking-widest hover:bg-warmBlack transition-all">
                                        Download Resume
                                    </a>
                                </div>
                                <div className="w-full h-[600px] bg-ivory/50 flex items-center justify-center border border-warmBrown/10">
                                    <iframe
                                        src={`http://localhost:8000/api/resume/download/${formData.resumeSettings?.defaultRegion || 'international'}#toolbar=0&navpanes=0&scrollbar=0`}
                                        width="100%"
                                        height="100%"
                                        className="bg-transparent"
                                        title="Resume PDF Preview"
                                    />
                                </div>
                            </div>
                            <button onClick={saveChanges} className="w-full py-4 bg-warmBrown text-ivory font-mono text-[10px] uppercase tracking-[0.3em] lg:col-span-2">Initialize Core Settings</button>
                        </div>
                    )}
                </div>
            </div>

            {/* Edit Modal */}
            <AnimatePresence>
                {editingItem && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setEditingItem(null)} className="absolute inset-0 bg-warmBlack/80 backdrop-blur-sm" />
                        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="bg-white w-full max-w-2xl relative z-10 p-12 shadow-2xl max-h-[90vh] overflow-y-auto">
                            <button onClick={() => setEditingItem(null)} className="absolute top-8 right-8 text-warmBrown/20 hover:text-accent">
                                <X size={20} />
                            </button>
                            <h3 className="text-3xl font-serif italic mb-8 capitalize">{editingItem.type} Editor</h3>

                            <div className="space-y-6">
                                {editingItem.type === 'experience' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Company" value={editingItem.item.company || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, company: e.target.value } })} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Role/Title" value={editingItem.item.role || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, role: e.target.value } })} />
                                        <div className="grid grid-cols-3 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Start Date (e.g. Jan 2023)" value={editingItem.item.startDate || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, startDate: e.target.value } })} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="End Date (e.g. Present)" value={editingItem.item.endDate || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, endDate: e.target.value } })} />
                                            <select className="w-full bg-transparent border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" value={editingItem.item.employment_type || 'Full-time'} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, employment_type: e.target.value } })}>
                                                <option value="Full-time">Full-time</option>
                                                <option value="Part-time">Part-time/Internship</option>
                                                <option value="Contract">Contract/Freelance</option>
                                            </select>
                                        </div>
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-24" placeholder="Description for AI (e.g. what you did)" value={editingItem.item.description || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, description: e.target.value } })} />

                                        <div className="flex justify-between items-center mt-2">
                                            <label className="text-[9px] font-mono text-warmBrown/40 uppercase tracking-widest">Bullets</label>
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    handleAIAction('generate-bullets', {
                                                        role: editingItem.item.role || '',
                                                        company: editingItem.item.company || '',
                                                        description: editingItem.item.description || ''
                                                    }, (newBullets) => setEditingItem({ ...editingItem, item: { ...editingItem.item, bullets: newBullets } }));
                                                }}
                                                className="text-accent hover:underline lowercase italic"
                                            >✦ generate bullets</button>
                                        </div>
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-32" placeholder="Bullets (One per line)" value={(editingItem.item.bullets || []).join('\n')} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, bullets: e.target.value.split('\n').filter(l => l.trim() !== '') } })} />
                                        
                                        <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold mt-4 pt-4 border-t border-warmBrown/10">Japan Metadata</h4>
                                        <div className="grid grid-cols-2 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="部署名 (Department)" value={editingItem.item.department || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, department: e.target.value } })} />
                                            <select className="w-full bg-transparent border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" value={editingItem.item.employment_type_ja || '正社員'} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, employment_type_ja: e.target.value } })}>
                                                <option value="正社員">正社員 (Full-time)</option>
                                                <option value="契約社員">契約社員 (Contract)</option>
                                                <option value="フリーランス">フリーランス (Freelance)</option>
                                                <option value="アルバイト">アルバイト (Part-time)</option>
                                            </select>
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" type="number" placeholder="チーム規模 (Team Size)" value={editingItem.item.team_size || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, team_size: e.target.value ? parseInt(e.target.value) : '' } })} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="退職理由 (Reason for leaving)" value={editingItem.item.resign_reason_ja || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, resign_reason_ja: e.target.value } })} />
                                        </div>
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-24 mt-2" placeholder="実績・成果 (Achievements - One per line)" value={(editingItem.item.achievements || []).join('\n')} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, achievements: e.target.value.split('\n').filter(l => l.trim() !== '') } })} />
                                    </>
                                )}

                                {editingItem.type === 'education' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="University" defaultValue={editingItem.item.university} onChange={e => editingItem.item.university = e.target.value} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Degree" defaultValue={editingItem.item.degree} onChange={e => editingItem.item.degree = e.target.value} />
                                        <div className="grid grid-cols-3 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px]" placeholder="Year (e.g. 2020 - 2022)" defaultValue={editingItem.item.year} onChange={e => editingItem.item.year = e.target.value} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px]" placeholder="Awarded" defaultValue={editingItem.item.awarded} onChange={e => editingItem.item.awarded = e.target.value} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px]" placeholder="GPA" defaultValue={editingItem.item.gpa} onChange={e => editingItem.item.gpa = e.target.value} />
                                        </div>
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-32 mt-4" placeholder="Notes (Optional)" defaultValue={editingItem.item.notes} onChange={e => editingItem.item.notes = e.target.value} />
                                    </>
                                )}

                                {editingItem.type === 'extracurriculars' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Program/Activity Name" value={editingItem.item.title || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, title: e.target.value } })} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Institution" value={editingItem.item.institution || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, institution: e.target.value } })} />
                                        <div className="grid grid-cols-2 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Duration (e.g. 2023/03 - 2024/02)" value={editingItem.item.duration || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, duration: e.target.value } })} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Type (e.g. 어학연수)" value={editingItem.item.type || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, type: e.target.value } })} />
                                        </div>
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-32 mt-4" placeholder="Bullets (One per line)" value={(editingItem.item.bullets || []).join('\n')} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, bullets: e.target.value.split('\n').filter(l => l.trim() !== '') } })} />
                                    </>
                                )}

                                {editingItem.type === 'certifications' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Certification Name" defaultValue={editingItem.item.name} onChange={e => editingItem.item.name = e.target.value} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Issuer (e.g. Coursera)" defaultValue={editingItem.item.issuer} onChange={e => editingItem.item.issuer = e.target.value} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Year" defaultValue={editingItem.item.year} onChange={e => editingItem.item.year = e.target.value} />
                                    </>
                                )}

                                {editingItem.type === 'projects' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Project Name" defaultValue={editingItem.item.name} onChange={e => editingItem.item.name = e.target.value} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-sans text-xs" placeholder="Tech Stack (Comma Separated)" defaultValue={editingItem.item.techStack?.join(', ')} onChange={e => editingItem.item.techStack = e.target.value.split(',').map(s => s.trim()).filter(s => s)} />
                                        <div className="grid grid-cols-2 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px]" placeholder="GitHub Link" defaultValue={editingItem.item.github} onChange={e => editingItem.item.github = e.target.value} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px]" placeholder="Live Link" defaultValue={editingItem.item.demo} onChange={e => editingItem.item.demo = e.target.value} />
                                        </div>
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-32" placeholder="Project Description" defaultValue={editingItem.item.description} onChange={e => editingItem.item.description = e.target.value} />
                                    </>
                                )}

                                {editingItem.type === 'achievements' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Achievement Title" defaultValue={editingItem.item.title} onChange={e => editingItem.item.title = e.target.value} />
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-32" placeholder="Brief Summary" defaultValue={editingItem.item.description} onChange={e => editingItem.item.description = e.target.value} />
                                    </>
                                )}

                                {editingItem.type === 'testimonials' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Name" defaultValue={editingItem.item.name} onChange={e => editingItem.item.name = e.target.value} />
                                        <div className="grid grid-cols-2 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Role" defaultValue={editingItem.item.role} onChange={e => editingItem.item.role = e.target.value} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Company" defaultValue={editingItem.item.company} onChange={e => editingItem.item.company = e.target.value} />
                                        </div>
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-32" placeholder="Quote" defaultValue={editingItem.item.quote} onChange={e => editingItem.item.quote = e.target.value} />
                                    </>
                                )}

                                {editingItem.type === 'research' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Topic" defaultValue={editingItem.item.topic} onChange={e => editingItem.item.topic = e.target.value} />
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-mono text-[10px] uppercase h-32" placeholder="Description (Compact)" defaultValue={editingItem.item.description} onChange={e => editingItem.item.description = e.target.value} />
                                    </>
                                )}

                                {editingItem.type === 'languages' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Language Name" defaultValue={editingItem.item.name} onChange={e => editingItem.item.name = e.target.value} />
                                        <div className="grid grid-cols-2 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Level (e.g. Native)" defaultValue={editingItem.item.level} onChange={e => editingItem.item.level = e.target.value} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" type="number" placeholder="Percentage" defaultValue={editingItem.item.percentage} onChange={e => editingItem.item.percentage = Number(e.target.value)} />
                                        </div>
                                    </>
                                )}

                                {editingItem.type === 'skills' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Category Label (e.g. ML & AI)" defaultValue={editingItem.item.label} onChange={e => editingItem.item.label = e.target.value} />
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-sans text-sm h-32" placeholder="Skills (Comma Separated)" defaultValue={editingItem.item.items?.join(', ')} onChange={e => editingItem.item.items = e.target.value.split(',').map(s => s.trim()).filter(s => s)} />
                                    </>
                                )}

                                {editingItem.type === 'activity' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Date (YYYY-MM-DD)" defaultValue={editingItem.item.date} onChange={e => editingItem.item.date = e.target.value} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Activity (e.g. Commited to Portfolio)" defaultValue={editingItem.item.activity} onChange={e => editingItem.item.activity = e.target.value} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" type="number" placeholder="Count" defaultValue={editingItem.item.count} onChange={e => editingItem.item.count = Number(e.target.value)} />
                                    </>
                                )}

                                {editingItem.type === 'blog' && (
                                    <>
                                        <input
                                            className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif"
                                            placeholder="Post Title"
                                            defaultValue={editingItem.item.title}
                                            onChange={e => {
                                                editingItem.item.title = e.target.value;
                                                // Auto slug injection
                                                if (!editingItem.item.id) {
                                                    editingItem.item.slug = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
                                                }
                                            }}
                                        />
                                        <div className="grid grid-cols-3 gap-4">
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Category" defaultValue={editingItem.item.category} onChange={e => editingItem.item.category = e.target.value} />
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" type="date" defaultValue={editingItem.item.date} onChange={e => editingItem.item.date = e.target.value} />
                                            <div className="flex items-center justify-end">
                                                <button
                                                    onClick={(e) => {
                                                        e.preventDefault();
                                                        const isDraft = editingItem.item.isDraft !== false; // default true
                                                        setEditingItem({ ...editingItem, item: { ...editingItem.item, isDraft: !isDraft, visible: isDraft } });
                                                    }}
                                                    className={`font-mono text-[9px] uppercase tracking-widest px-4 py-2 border transition-all ${editingItem.item.isDraft === false ? 'border-green-600/30 text-green-600 bg-green-50' : 'border-warmBrown/20 text-warmBrown/50 hover:bg-warmBrown/5'}`}
                                                >
                                                    {editingItem.item.isDraft === false ? '[ PUBLISHED ]' : '[ DRAFT ]'}
                                                </button>
                                            </div>
                                        </div>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px] text-warmBrown/40" placeholder="Slug (Auto-generated)" value={editingItem.item.slug || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, slug: e.target.value } })} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="External URL (Optional - Redirects instead of opening modal)" defaultValue={editingItem.item.url} onChange={e => editingItem.item.url = e.target.value} />
                                        <textarea className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-mono text-xs h-64" placeholder="Content (Markdown Supported)" defaultValue={editingItem.item.content} onChange={e => editingItem.item.content = e.target.value} />
                                    </>
                                )}

                                {editingItem.type === 'connections' && (
                                    <>
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-serif" placeholder="Platform (e.g. YouTube, Instagram, KakaoTalk)" value={editingItem.item.platform || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, platform: e.target.value } })} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="URL (e.g. https://youtube.com/@handle)" value={editingItem.item.url || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, url: e.target.value } })} />
                                        <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-xs" placeholder="Handle/Username (e.g. @divyanirankari)" value={editingItem.item.handle || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, handle: e.target.value } })} />
                                        
                                        <div className="flex items-center gap-4 bg-ivory/20 p-4 border border-warmBrown/5 mt-4">
                                            <div className="flex-1">
                                                <h4 className="font-mono text-[10px] uppercase tracking-widest text-warmBrown">Icon Signal</h4>
                                                <p className="text-[9px] text-warmBrown/40 uppercase">Automatically mapped based on Platform name</p>
                                            </div>
                                            <div className="text-accent font-mono text-[10px] lowercase italic">
                                                {(['github', 'linkedin', 'youtube', 'instagram', 'slack', 'skype', 'email', 'kakaotalk'].includes(editingItem.item.platform?.toLowerCase())) 
                                                  ? '✓ Signal Match Found' 
                                                  : '⚠ Generic Signal Active'}
                                            </div>
                                        </div>
                                    </>
                                )}

                                <button
                                    onClick={() => {
                                        const keyMap = {
                                            experience: 'experience',
                                            education: 'education',
                                            extracurriculars: 'extracurriculars',
                                            certifications: 'certifications',
                                            achievements: 'achievements',
                                            testimonials: 'testimonials',
                                            research: 'researchInterests',
                                            languages: 'languages',
                                            blog: 'blogPosts',
                                            projects: 'projects',
                                            skills: 'skillCategories',
                                            activity: 'activityLog',
                                            connections: 'connections'
                                        };
                                        const key = keyMap[editingItem.type];
                                        if (!editingItem.item.id) {
                                            // It's a new item (no ID assigned yet)
                                            const newItems = [...(formData[key] || []), { ...editingItem.item, id: Date.now().toString(), visible: true, order: (formData[key]?.length || 0) }];
                                            setFormData(prev => ({ ...prev, [key]: newItems }));
                                        } else {
                                            // It's an update - we already mutated the item in the modal, 
                                            // but we should trigger a state update to ensure persistence
                                            setFormData(prev => ({ ...prev }));
                                        }
                                        setEditingItem(null);
                                    }}
                                    className="w-full py-4 bg-warmBrown text-ivory font-mono text-xs uppercase tracking-[0.4em] hover:bg-black transition-all"
                                >
                                    Index Artifact
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Admin;
