import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AdminContext } from '../context/AdminContext';
import { PortfolioContext } from '../context/PortfolioContext';
import { motion, AnimatePresence } from 'framer-motion';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

import MessageInbox from '../components/MessageInbox';
import CollectionEditor from '../components/CollectionEditor';
import { Layout, FileText, BarChart3, ListTree, Settings as SettingsIcon, ShieldCheck, X, Eye, Download, RefreshCw, Maximize2, Copy, CheckCircle2, Info, Languages, Trash2, ShieldAlert } from 'lucide-react';

const Admin = () => {
    const { isAuthenticated, login, logout, token } = useContext(AdminContext);
    const { data, fetchPortfolio, updatePortfolio } = useContext(PortfolioContext);
    const navigate = useNavigate();

    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [command, setCommand] = useState('');
    const [cmdResult, setCmdResult] = useState(null);
    const [activeTab, setActiveTab] = useState('dashboard');
    const [previewRegion, setPreviewRegion] = useState('international');
    const [previewCountry, setPreviewCountry] = useState('usa');
    const [previewLanguage, setPreviewLanguage] = useState('en');
    const [includeCoverLetter, setIncludeCoverLetter] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isGeneratingCL, setIsGeneratingCL] = useState(false);
    const [editingItem, setEditingItem] = useState(null); // { type, item }

    // Local state for edits
    const [formData, setFormData] = useState(null);
    const [resumeFile, setResumeFile] = useState(null);
    const [allProjects, setAllProjects] = useState([]);
    const [toastMessage, setToastMessage] = useState(null);
    const [translations, setTranslations] = useState([]);
    const [isLoadingTranslations, setIsLoadingTranslations] = useState(false);
    const [showDownloadPrompt, setShowDownloadPrompt] = useState(false);
    const [isVerifyingBeforeDownload, setIsVerifyingBeforeDownload] = useState(false);
    const [verificationLang, setVerificationLang] = useState('en');
    const [atsScore, setAtsScore] = useState(0);
    const [atsChecks, setAtsChecks] = useState([]);

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

    const saveChanges = async (msg = 'Artifacts Deposited Successfully') => {
        const toastMsg = typeof msg === 'string' ? msg : 'Artifacts Deposited Successfully';
        const success = await updatePortfolio(formData);
        if (success) {
            showToast(toastMsg, 'success');
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

    const fetchTranslations = async () => {
        setIsLoadingTranslations(true);
        try {
            const res = await fetch('http://localhost:8000/api/admin/translations/');
            const data = await res.json();
            setTranslations(data);
        } catch (err) {
            showToast('Failed to load translations', 'error');
        } finally {
            setIsLoadingTranslations(false);
        }
    };

    const updateTranslation = async (id, text, verified) => {
        try {
            await fetch('http://localhost:8000/api/admin/translations/update/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, translated_text: text, is_verified: verified })
            });
            showToast('Translation Signal Stabilized');
            fetchTranslations();
            // Force reload the target iframe in the verification suite if it exists
            const targetIframe = document.getElementById('verification-iframe-target');
            if (targetIframe) {
                targetIframe.src = targetIframe.src.split('&v=')[0] + '&v=' + Date.now();
            }
        } catch (err) {
            showToast('Failed to update signal', 'error');
        }
    };

    const deleteTranslation = async (id) => {
        if (!window.confirm('Terminate this translation signal?')) return;
        try {
            await fetch(`http://localhost:8000/api/admin/translations/${id}`, { method: 'DELETE' });
            showToast('Signal Terminated');
            fetchTranslations();
        } catch (err) {
            showToast('Failed to terminate signal', 'error');
        }
    };

    const clearUnverified = async () => {
        if (!window.confirm('Wipe all unverified translation signals?')) return;
        try {
            await fetch('http://localhost:8000/api/admin/translations/clear-cache/', { method: 'POST' });
            showToast('Neural Cache Purged');
            fetchTranslations();
        } catch (err) {
            showToast('Purge Failed', 'error');
        }
    };

    useEffect(() => {
        if (activeTab === 'translations') {
            fetchTranslations();
        }
    }, [activeTab]);

    const fetchATSScore = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/resume/ats-score/${previewCountry}`);
            const data = await res.json();
            setAtsScore(data.score);
            setAtsChecks(data.checks);
        } catch (err) {
            console.error('Failed to fetch ATS score');
        }
    };

    useEffect(() => {
        if (activeTab === 'preview') {
            fetchATSScore();
        }
    }, [previewCountry, data, activeTab]);

    // Neural Scroll Synchronization for Verification Suite
    useEffect(() => {
        if (!isVerifyingBeforeDownload) return;

        const setupSync = () => {
            const iframeEn = document.getElementById('verification-iframe-en');
            const iframeTarget = document.getElementById('verification-iframe-target');
            
            if (!iframeEn || !iframeTarget) return;

            let isSyncing = false;

            const handleScroll = (source, target) => {
                if (isSyncing) return;
                isSyncing = true;
                try {
                    const sourceDoc = source.contentDocument || source.contentWindow.document;
                    const targetDoc = target.contentDocument || target.contentWindow.document;
                    if (!sourceDoc || !targetDoc) return;
                    
                    const scrollPercent = sourceDoc.documentElement.scrollTop / (sourceDoc.documentElement.scrollHeight - sourceDoc.documentElement.clientHeight);
                    const targetScrollTop = scrollPercent * (targetDoc.documentElement.scrollHeight - targetDoc.documentElement.clientHeight);
                    targetDoc.documentElement.scrollTop = targetScrollTop;
                } catch (e) {
                    // Possible cross-origin or frame not ready
                }
                setTimeout(() => { isSyncing = false; }, 50);
            };

            const attachListener = (iframe, other) => {
                try {
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (doc) {
                        iframe.contentWindow.onscroll = () => handleScroll(iframe, other);
                        // Also try the doc itself for redundancy
                        doc.onscroll = () => handleScroll(iframe, other);
                    }
                } catch (e) {}
            };

            // Attempt initial attachment
            attachListener(iframeEn, iframeTarget);
            attachListener(iframeTarget, iframeEn);

            // Re-attach on load to ensure we have the internal window context
            iframeEn.onload = () => attachListener(iframeEn, iframeTarget);
            iframeTarget.onload = () => attachListener(iframeTarget, iframeEn);
        };

        const timer = setTimeout(setupSync, 1500); // Wait for initial render
        return () => clearTimeout(timer);
    }, [isVerifyingBeforeDownload, activeTab]);

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

    const handleExportClick = () => {
        if (['japan', 'korea', 'china'].includes(previewCountry)) {
            setShowDownloadPrompt(true);
        } else {
            // Direct download for others (they stay in English or selected lang)
            triggerDownload(previewLanguage);
        }
    };

    const handleNativeChoice = () => {
        const lang = previewCountry === 'japan' ? 'ja' : previewCountry === 'korea' ? 'ko' : 'zh';
        setVerificationLang(lang);
        setIsVerifyingBeforeDownload(true);
        fetchTranslations(); // Ensure latest data is loaded
    };

    const triggerDownload = (lang) => {
        const url = `http://localhost:8000/api/resume/download/${previewCountry}?lang=${lang}&cover=${includeCoverLetter}&download=true&v=${Date.now()}`;
        window.open(url, '_blank');
        setShowDownloadPrompt(false);
        setIsVerifyingBeforeDownload(false);
    };

    const tabs = [
        { id: 'dashboard', label: 'Monitor', icon: <BarChart3 size={14} /> },
        { id: 'content', label: 'Identity', icon: <FileText size={14} /> },
        { id: 'collections', label: 'Artifacts', icon: <ListTree size={14} /> },
        { id: 'cover_letter', label: 'Cover Letter', icon: <FileText size={14} /> },
        { id: 'preview', label: 'Resume Preview', icon: <Eye size={14} /> },
        { id: 'settings', label: 'Core', icon: <SettingsIcon size={14} /> }
    ];

    return (
        <div className="min-h-screen bg-ivory pt-8 pb-32 px-6 relative z-20 overflow-x-hidden">
            {/* Subtle Background Pattern */}
            <div className="fixed inset-0 pointer-events-none opacity-[0.03] z-[-1]" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` }} />
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
                            <p className="font-mono text-[10px] uppercase tracking-widest text-warmBrown/30 mt-1">Authorized Access Only // Port 8000</p>
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
                                {['name', 'role', 'email', 'phone', 'alternate_phone', 'location', 'summary', 'bio'].map(field => (
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
                                <button onClick={() => saveChanges('Data preserved successfully')} className="w-full py-4 bg-warmBrown text-ivory font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-black transition-all">Preserve Identity</button>
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
                                    <button onClick={() => saveChanges('Narrative committed successfully')} className="w-full py-4 bg-warmBrown text-ivory font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-black transition-all">Commit Narrative</button>
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
                                    <button onClick={() => saveChanges('Metrics synced successfully')} className="w-full py-4 bg-accent text-ivory font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-warmBlack transition-all">Sync Metrics</button>
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
                            <button onClick={() => saveChanges('Artifacts deposited successfully')} className="fixed bottom-8 right-8 w-48 py-4 bg-accent text-white font-mono text-xs shadow-2xl z-50 hover:bg-warmBlack transition-all uppercase tracking-widest">Deposit Artifacts</button>
                        </div>
                    )}

                    {activeTab === 'cover_letter' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-32">
                            <div className="bg-white p-8 border border-warmBrown/5 shadow-sm space-y-6">
                                <h3 className="font-serif text-2xl border-b border-warmBrown/5 pb-6 flex justify-between items-center italic">
                                    자기소개서 (Cover Letter)
                                    <button
                                        onClick={async () => {
                                            setIsGeneratingCL(true);
                                            showToast('Synthesizing Universal Cover Letter...', 'success');
                                            try {
                                                const res = await fetch('http://localhost:8000/api/admin/generate-cover-letter/', {
                                                    method: 'POST',
                                                    headers: { 'Content-Type': 'application/json' },
                                                    body: JSON.stringify({
                                                        about: formData.about || [],
                                                        experience: formData.experience || [],
                                                        region: previewRegion,
                                                        lang: previewLanguage
                                                    })
                                                });
                                                const cl = await res.json();
                                                setFormData(prev => ({
                                                    ...prev,
                                                    cover_letter: {
                                                        ...(prev.cover_letter || {}),
                                                        ...cl
                                                    },
                                                    // Map Japanese specific PR if returned
                                                    personal: cl.self_pr_ja ? { ...(prev.personal || {}), self_pr_ja: cl.self_pr_ja } : prev.personal
                                                }));
                                                showToast('Cover Letter Synthesized Successfully');
                                            } catch (err) {
                                                showToast('AI Synthesis Failed: ' + err.message, 'error');
                                            } finally {
                                                setIsGeneratingCL(false);
                                            }
                                        }}
                                        disabled={isGeneratingCL}
                                        className={`bg-accent text-white px-6 py-2 font-mono text-[10px] uppercase tracking-widest hover:bg-warmBlack transition-all flex items-center gap-2 rounded-lg ${isGeneratingCL ? 'animate-pulse opacity-50' : ''}`}
                                    >
                                        {isGeneratingCL ? '✦ Processing Signal...' : '✦ Generate AI Version'}
                                    </button>
                                </h3>

                                <div className="grid grid-cols-1 gap-8">
                                    {/* Global Content Field */}
                                    <div className="space-y-3">
                                        <label className="block text-[10px] font-mono text-accent font-bold uppercase tracking-widest">Global Body (International / Japan / China)</label>
                                        <textarea
                                            className="w-full border border-warmBrown/10 p-6 focus:outline-none focus:border-accent font-serif text-sm h-64 bg-ivory/5 leading-relaxed"
                                            value={formData.cover_letter?.content || ''}
                                            onChange={e => setFormData(prev => ({
                                                ...prev,
                                                cover_letter: {
                                                    ...(prev.cover_letter || {}),
                                                    content: e.target.value
                                                }
                                            }))}
                                            placeholder="Standard cover letter body used for non-Korean templates..."
                                        />
                                    </div>

                                    {/* Korean Specific Sections */}
                                    <div className="pt-8 border-t border-warmBrown/5 space-y-8">
                                        <h4 className="font-mono text-[10px] text-warmBrown/30 uppercase tracking-[0.3em]">Korean Specialty Sections (자기소개서)</h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {[
                                                { id: 'growth_background', label: '1. 성장과정 (Growth)' },
                                                { id: 'strengths_weaknesses', label: '2. 장단점 (Traits)' },
                                                { id: 'motivation', label: '3. 지원동기 (Motivation)' },
                                                { id: 'goals_after_joining', label: '4. 포부 (Goals)' }
                                            ].map(section => (
                                                <div key={section.id} className="space-y-3">
                                                    <label className="block text-[9px] font-mono text-warmBrown/40 uppercase tracking-widest">{section.label}</label>
                                                    <textarea
                                                        className="w-full border border-warmBrown/10 p-4 focus:outline-none focus:border-accent font-serif text-[13px] h-40 bg-ivory/5 leading-relaxed"
                                                        value={formData.cover_letter?.[section.id] || ''}
                                                        onChange={e => setFormData(prev => ({
                                                            ...prev,
                                                            cover_letter: {
                                                                ...(prev.cover_letter || {}),
                                                                [section.id]: e.target.value
                                                            }
                                                        }))}
                                                        placeholder={`[Korean ${section.id}]`}
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                                <button onClick={() => saveChanges('Cover Letter archived successfully')} className="w-full py-4 bg-warmBrown text-ivory font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-black transition-all rounded-xl shadow-lg">Archive Global Cover Letter</button>
                            </div>
                        </div>
                    )}

                    {activeTab === 'preview' && (
                        <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700 h-[88vh]">
                            {/* Toolbar */}
                            <div className="flex items-center gap-6 bg-white/80 backdrop-blur-xl p-6 border border-warmBrown/10 shadow-lg rounded-xl">
                                <div className="flex items-center gap-6">
                                    <div className="flex flex-col gap-1.5">
                                        <label className="font-mono text-[8px] uppercase tracking-[0.3em] text-accent font-bold">Country Context</label>
                                        <select 
                                            className="border-none py-1 focus:outline-none focus:ring-0 font-serif text-xl bg-transparent italic text-warmBrown cursor-pointer hover:text-accent transition-all"
                                            value={previewCountry}
                                            onChange={(e) => {
                                                setIsRefreshing(true);
                                                setPreviewCountry(e.target.value);
                                                const country = e.target.value;
                                                if (['japan', 'korea', 'china'].includes(country)) {
                                                    setPreviewRegion(country);
                                                    setIncludeCoverLetter(true);
                                                } else {
                                                    setPreviewRegion('international');
                                                    setIncludeCoverLetter(false);
                                                }
                                            }}
                                        >
                                            <option value="usa">USA (Standard ATS)</option>
                                            <option value="uk">United Kingdom</option>
                                            <option value="germany">Germany (DACH)</option>
                                            <option value="uae">UAE / Middle East</option>
                                            <option value="japan">Japan (Specialty)</option>
                                            <option value="korea">South Korea (Specialty)</option>
                                            <option value="china">China (Mainland)</option>
                                            <option value="international">Global / International</option>
                                        </select>
                                    </div>

                                    <div className="h-10 w-px bg-warmBrown/10" />

                                    <div className="flex flex-col gap-1.5">
                                        <label className="font-mono text-[8px] uppercase tracking-[0.3em] text-accent font-bold">Language</label>
                                        <select 
                                            className="border-none py-1 focus:outline-none focus:ring-0 font-serif text-lg bg-transparent italic text-warmBrown/60 cursor-pointer hover:text-accent transition-all"
                                            value={previewLanguage}
                                            onChange={(e) => {
                                                setIsRefreshing(true);
                                                setPreviewLanguage(e.target.value);
                                            }}
                                        >
                                            <option value="en">English (Global)</option>
                                            <option value="ko">Korean (한국어)</option>
                                            <option value="ja">Japanese (日本語)</option>
                                            <option value="zh">Chinese (简体中文)</option>
                                            <option value="de">German (Deutsch)</option>
                                        </select>
                                    </div>

                                    <div className="h-10 w-px bg-warmBrown/10" />

                                    <div className="flex items-center gap-3 bg-ivory/20 px-4 py-2 rounded-lg border border-warmBrown/5">
                                        <label className="font-mono text-[8px] uppercase tracking-widest text-warmBrown/40">Cover Letter</label>
                                        <button 
                                            onClick={() => {
                                                setIsRefreshing(true);
                                                setIncludeCoverLetter(!includeCoverLetter);
                                            }}
                                            className={`w-10 h-5 rounded-full relative transition-colors ${includeCoverLetter ? 'bg-accent' : 'bg-warmBrown/10'}`}
                                        >
                                            <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${includeCoverLetter ? 'left-6' : 'left-1'}`} />
                                        </button>
                                    </div>
                                </div>

                                <div className="ml-auto flex items-center gap-4">
                                    <button 
                                        onClick={() => {
                                            setIsRefreshing(true);
                                            const iframe = document.getElementById('preview-iframe');
                                            if (iframe) iframe.src = iframe.src;
                                        }}
                                        className={`p-3.5 border border-warmBrown/10 rounded-full text-warmBrown/40 hover:text-accent hover:border-accent/30 transition-all bg-white shadow-sm hover:shadow-md ${isRefreshing ? 'animate-spin text-accent border-accent/20' : ''}`}
                                        title="Reload Engine"
                                    >
                                        <RefreshCw size={16} />
                                    </button>

                                    <button 
                                        onClick={() => {
                                            navigator.clipboard.writeText(`http://localhost:8000/api/resume/preview/${previewCountry}?lang=${previewLanguage}&cover=${includeCoverLetter}`);
                                            showToast('Preview link copied to clipboard');
                                        }}
                                        className="p-3.5 border border-warmBrown/10 rounded-full text-warmBrown/40 hover:text-accent hover:border-accent/30 transition-all bg-white shadow-sm"
                                        title="Copy HTML Link"
                                    >
                                        <Copy size={16} />
                                    </button>

                                    <div className="h-10 w-px bg-warmBrown/10 mx-2" />

                                    <button 
                                        onClick={handleExportClick}
                                        className="flex items-center gap-4 px-8 py-3.5 bg-warmBrown text-ivory font-mono text-[11px] uppercase tracking-[0.25em] hover:bg-black transition-all shadow-xl hover:shadow-black/20 group rounded-lg"
                                    >
                                        <Download size={16} className="group-hover:translate-y-0.5 transition-transform" />
                                        Export PDF
                                    </button>
                                </div>
                            </div>

                            {/* Document Viewer Frame */}
                            <div className="flex-1 flex gap-6 overflow-hidden border-2 border-warmBrown/10 p-6 rounded-2xl bg-white/30 backdrop-blur-sm">
                                <div className="flex-1 bg-ivory/20 border border-warmBrown/10 shadow-inner rounded-2xl overflow-hidden relative group flex flex-col">
                                    {/* Mock Browser Header */}
                                    <div className="h-10 bg-white/50 border-b border-warmBrown/5 flex items-center px-4 gap-2">
                                        <div className="flex gap-1.5">
                                            <div className="w-2.5 h-2.5 rounded-full bg-red-400/20" />
                                            <div className="w-2.5 h-2.5 rounded-full bg-amber-400/20" />
                                            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/20" />
                                        </div>
                                        <div className="mx-auto bg-white/80 px-4 py-1 rounded-md border border-warmBrown/5 flex items-center gap-2">
                                            <ShieldCheck size={10} className="text-accent" />
                                            <span className="font-mono text-[9px] text-warmBrown/30 lowercase">localhost:8000/api/resume/preview/{previewCountry}?lang={previewLanguage}&cover={includeCoverLetter.toString()}</span>
                                        </div>
                                        <button className="text-warmBrown/20 hover:text-accent transition-colors">
                                            <Maximize2 size={14} />
                                        </button>
                                    </div>

                                    <div className="flex-1 relative">
                                        {isRefreshing && (
                                            <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-20 flex items-center justify-center animate-in fade-in duration-300">
                                                <div className="flex flex-col items-center gap-4">
                                                    <div className="w-12 h-12 border-4 border-accent/20 border-t-accent rounded-full animate-spin" />
                                                    <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-warmBrown/60">Rebuilding Engine...</span>
                                                </div>
                                            </div>
                                        )}
                                        <iframe 
                                            id="preview-iframe"
                                            src={`http://localhost:8000/api/resume/preview/${previewCountry}?lang=${previewLanguage}&cover=${includeCoverLetter}`} 
                                            className="w-full h-full border-none bg-white custom-scrollbar"
                                            onLoad={() => setIsRefreshing(false)}
                                            title="Resume Preview"
                                        />
                                    </div>
                                </div>

                                {/* Sidebar Stats */}
                                <div className="w-64 flex flex-col gap-4">
                                    <div className="bg-white p-6 border border-warmBrown/10 shadow-sm rounded-xl space-y-4">
                                        <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold flex items-center gap-2">
                                            <div className="w-2 h-2 bg-accent rounded-full" /> Compliance Status
                                        </h4>
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between text-[10px] font-mono">
                                                <span className="text-warmBrown/40 uppercase">Country</span>
                                                <span className="text-warmBrown font-bold capitalize">{previewCountry}</span>
                                            </div>
                                            <div className="flex items-center justify-between text-[10px] font-mono">
                                                <span className="text-warmBrown/40 uppercase">Language</span>
                                                <span className="text-warmBrown font-bold uppercase">{previewLanguage}</span>
                                            </div>
                                            <div className="flex items-center justify-between text-[10px] font-mono">
                                                <span className="text-warmBrown/40 uppercase">Template</span>
                                                <span className="text-warmBrown">v8.2 Final</span>
                                            </div>
                                            
                                            <div className="pt-2 border-t border-warmBrown/5 space-y-2">
                                                <div className="flex items-center justify-between text-[9px] font-mono">
                                                    <span className="text-warmBrown/40">PHOTO POLICY</span>
                                                    <span className={`${['usa', 'uk', 'international'].includes(previewCountry) ? 'text-emerald-600' : 'text-amber-600'} font-bold`}>
                                                        {['usa', 'uk', 'international'].includes(previewCountry) ? 'HIDDEN' : 'SHOWN'}
                                                    </span>
                                                </div>
                                                <div className="flex items-center justify-between text-[9px] font-mono">
                                                    <span className="text-warmBrown/40">DOB POLICY</span>
                                                    <span className={`${['usa', 'uk'].includes(previewCountry) ? 'text-emerald-600' : 'text-amber-600'} font-bold`}>
                                                        {['usa', 'uk'].includes(previewCountry) ? 'HIDDEN' : 'SHOWN'}
                                                    </span>
                                                </div>
                                                <div className="flex items-center justify-between text-[9px] font-mono">
                                                    <span className="text-warmBrown/40">COVER LETTER</span>
                                                    <span className={`${includeCoverLetter ? 'text-emerald-600' : 'text-warmBrown/20'} font-bold`}>
                                                        {includeCoverLetter ? 'INCLUDED' : 'SKIPPED'}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2 text-[9px] text-emerald-600 font-bold italic pt-1">
                                                    <CheckCircle2 size={10} /> ATS COMPATIBLE
                                                </div>
                                            </div>

                                            <div className="pt-3 border-t border-warmBrown/5">
                                                <div className="flex justify-between items-center mb-1.5">
                                                    <span className="font-mono text-[8px] uppercase text-warmBrown/40">ATS Score</span>
                                                    <span className={`font-mono text-[10px] font-bold ${atsScore > 80 ? 'text-emerald-600' : atsScore > 50 ? 'text-amber-600' : 'text-red-500'}`}>{atsScore} / 100</span>
                                                </div>
                                                <div className="w-full h-2 bg-warmBrown/5 rounded-full overflow-hidden p-[1px]">
                                                    <div 
                                                        className={`h-full transition-all duration-1000 rounded-full relative ${atsScore > 80 ? 'bg-emerald-500' : atsScore > 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                                                        style={{ width: `${atsScore}%` }}
                                                    >
                                                        <div className="absolute inset-0 bg-white/20 animate-pulse" />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="pt-4 space-y-2">
                                                {atsChecks.map((check, i) => (
                                                    <div key={i} className="flex items-start gap-2 text-[8px] font-mono text-warmBrown/60">
                                                        <CheckCircle2 size={10} className="text-emerald-500 mt-0.5 shrink-0" />
                                                        <span>{check}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-warmBrown/5 p-6 border border-warmBrown/10 rounded-xl space-y-3">
                                        <h4 className="font-serif text-sm italic text-warmBrown">Quick Tips</h4>
                                        <p className="text-[10px] text-warmBrown/80 leading-relaxed font-sans font-medium">
                                            {previewCountry === 'usa' ? 'USA ATS format strictly forbids photos and DOB to comply with non-bias hiring laws.' : 
                                             previewCountry === 'korea' ? 'South Korea (Kowork) style includes personal photos and specific dual-column sorting logic.' : 
                                             previewCountry === 'japan' ? 'Japan (Rirekisho) requires ERA-based dates and specific marital status indicators.' :
                                             'Regional layout rules applied. Sorting and localization labels are dynamically injected.'}
                                        </p>
                                    </div>
                                </div>
                            </div>
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

                            {/* Visual Engine Config */}
                            <div className="bg-white/80 backdrop-blur-xl p-10 border border-warmBrown/10 shadow-xl rounded-3xl space-y-8">
                                <div className="space-y-2">
                                    <h3 className="font-serif text-3xl italic text-warmBrown">Visual Architecture</h3>
                                    <p className="font-mono text-[9px] uppercase tracking-widest text-warmBrown/40">Canvas & Rendering Controls</p>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center bg-ivory/40 p-6 border border-warmBrown/5 rounded-2xl hover:border-accent/20 transition-all group">
                                        <div className="flex flex-col gap-1">
                                            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-warmBrown font-bold">3D Particle Hero</span>
                                            <span className="text-[9px] text-warmBrown/40 italic">WebGL Fractal Noise Background</span>
                                        </div>
                                        <button
                                            onClick={() => {
                                                const newVal = formData.settings?.hero3d !== false ? false : true;
                                                setFormData(prev => ({
                                                    ...prev,
                                                    settings: { ...(prev.settings || {}), hero3d: newVal }
                                                }));
                                            }}
                                            className={`px-6 py-2 rounded-full border font-mono text-[9px] tracking-widest transition-all ${formData.settings?.hero3d !== false ? 'bg-accent/10 border-accent text-accent shadow-[0_0_15px_rgba(var(--accent-rgb),0.2)]' : 'bg-warmBrown/5 border-warmBrown/10 text-warmBrown/30 hover:border-warmBrown/30'}`}
                                        >
                                            {formData.settings?.hero3d !== false ? 'SIGNAL_ACTIVE' : 'SIGNAL_DORMANT'}
                                        </button>
                                    </div>

                                    <div className="bg-warmBrown/[0.02] p-8 border border-dashed border-warmBrown/10 rounded-2xl">
                                        <div className="flex items-center gap-4 mb-6">
                                            <div className="w-2 h-2 bg-accent rounded-full animate-ping" />
                                            <h4 className="font-mono text-[9px] uppercase tracking-widest text-warmBrown/60">Logic Pipeline Status</h4>
                                        </div>
                                        <div className="space-y-4">
                                            {[
                                                { label: 'Frontend Sync', status: 'Optimal', val: '98%' },
                                                { label: 'PDF Generation', status: 'Stable', val: '100%' },
                                                { label: 'AI Synthesis', status: 'Awaiting', val: 'Groq' }
                                            ].map(item => (
                                                <div key={item.label} className="flex items-center justify-between">
                                                    <span className="font-mono text-[8px] text-warmBrown/40">{item.label}</span>
                                                    <div className="flex-1 mx-4 h-px bg-warmBrown/5" />
                                                    <span className="font-mono text-[8px] text-warmBrown font-bold">{item.val}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Terminal AI Section */}
                            <div className="bg-warmBlack p-10 border border-accent/20 shadow-2xl rounded-3xl space-y-8 group">
                                <div className="flex justify-between items-center">
                                    <div className="space-y-1">
                                        <h3 className="font-mono text-[10px] uppercase tracking-[0.4em] text-accent font-bold flex items-center gap-3">
                                            <div className="w-2 h-2 bg-accent rounded-full shadow-[0_0_10px_#cc9b7a]" />
                                            Terminal_AI_Interface
                                        </h3>
                                        <p className="font-mono text-[7px] uppercase text-ivory/20">System V8.2 // Root Authority</p>
                                    </div>
                                    <ShieldCheck size={16} className="text-accent/40 group-hover:text-accent transition-colors" />
                                </div>

                                <form onSubmit={handleCommand} className="relative">
                                    <div className="absolute left-0 top-3 text-accent font-mono text-xs opacity-50">&gt;</div>
                                    <input
                                        type="text"
                                        placeholder="Invoke command sequence..."
                                        className="w-full border-b border-accent/10 p-3 pl-6 font-mono text-xs focus:outline-none focus:border-accent bg-transparent text-ivory placeholder:text-ivory/10 transition-all"
                                        value={command}
                                        onChange={(e) => setCommand(e.target.value)}
                                    />
                                    <button type="submit" className="absolute right-0 bottom-2 text-accent font-mono text-[9px] uppercase tracking-widest hover:text-white transition-colors">Execute</button>
                                </form>

                                <div className="min-h-[200px] bg-black/40 border border-white/5 p-6 rounded-xl font-mono text-[10px] leading-relaxed text-ivory/60 overflow-y-auto max-h-64 custom-scrollbar">
                                    {cmdResult ? (
                                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                            <span className="text-accent/60"># SEQUENCE_SUCCESSFUL</span>
                                            <br /><br />
                                            {cmdResult}
                                        </motion.div>
                                    ) : (
                                        <span className="opacity-20 animate-pulse">Awaiting input...</span>
                                    )}
                                </div>
                            </div>

                            <button onClick={() => saveChanges('Core settings initialized successfully')} className="lg:col-span-2 w-full py-6 bg-warmBrown text-ivory font-mono text-xs uppercase tracking-[0.5em] hover:bg-black transition-all shadow-2xl rounded-2xl flex items-center justify-center gap-4 group">
                                <ShieldCheck size={16} className="group-hover:scale-110 transition-transform" />
                                Commit System Changes
                            </button>
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
                                        
                                        <div className="mt-4 p-4 border border-warmBrown/10 bg-ivory/20 space-y-4">
                                            <h4 className="font-mono text-[10px] uppercase tracking-widest text-accent font-bold">Image Override</h4>
                                            <p className="text-[9px] font-sans text-warmBrown/60">Upload an image or provide a URL to override the auto-detected GitHub README image.</p>
                                            
                                            {editingItem.item.image_override && (
                                                <div className="h-32 bg-white border border-warmBrown/10 flex items-center justify-center overflow-hidden">
                                                    <img src={editingItem.item.image_override.startsWith('http') ? editingItem.item.image_override : `http://localhost:8000/${editingItem.item.image_override}`} alt="Preview" className="max-h-full object-contain" />
                                                </div>
                                            )}
                                            
                                            <input className="w-full border-b border-warmBrown/10 py-2 focus:outline-none focus:border-accent font-mono text-[10px]" placeholder="Image URL (http://...)" value={editingItem.item.image_override || ''} onChange={e => setEditingItem({ ...editingItem, item: { ...editingItem.item, image_override: e.target.value } })} />
                                            
                                            <div className="flex items-center gap-4">
                                                <input
                                                    type="file"
                                                    accept="image/*"
                                                    className="hidden"
                                                    id="project-image-upload"
                                                    onChange={async (e) => {
                                                        const file = e.target.files[0];
                                                        if (!file) return;
                                                        const uploadData = new FormData();
                                                        uploadData.append('file', file);
                                                        try {
                                                            const res = await fetch('http://localhost:8000/api/admin/project-image/', {
                                                                method: 'POST',
                                                                body: uploadData
                                                            });
                                                            const resJson = await res.json();
                                                            if (resJson.url) {
                                                                setEditingItem({ ...editingItem, item: { ...editingItem.item, image_override: resJson.url } });
                                                                showToast('Project Image Decanted Successfully');
                                                            }
                                                        } catch (err) {
                                                            showToast('Image upload failed', 'error');
                                                        }
                                                    }}
                                                />
                                                <label htmlFor="project-image-upload" className="inline-block px-4 py-2 border border-warmBrown/20 font-mono text-[9px] uppercase tracking-widest cursor-pointer hover:bg-warmBrown hover:text-ivory transition-all">
                                                    Upload Local Image
                                                </label>
                                                {editingItem.item.image_override && (
                                                    <button onClick={() => setEditingItem({ ...editingItem, item: { ...editingItem.item, image_override: "" } })} className="px-4 py-2 border border-red-500/20 text-red-500 font-mono text-[9px] uppercase tracking-widest hover:bg-red-50 transition-all">
                                                        Clear Override
                                                    </button>
                                                )}
                                            </div>
                                        </div>
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

            {/* Global Status Bar (Improvisation) */}
            <div className="fixed bottom-0 left-0 right-0 h-10 bg-warmBlack border-t border-accent/20 flex items-center px-6 gap-8 z-[150] shadow-[0_-10px_30px_rgba(0,0,0,0.2)]">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
                    <span className="font-mono text-[9px] uppercase tracking-widest text-ivory/60">System Operational</span>
                </div>
                <div className="h-4 w-px bg-white/10" />
                <div className="flex items-center gap-4 text-[8px] font-mono uppercase tracking-[0.2em] text-ivory/40">
                    <span className="hover:text-accent transition-colors cursor-default">DB: SQLITE_MASTER</span>
                    <span className="hover:text-accent transition-colors cursor-default">AI: GROQ_LLAMA3_ACTIVE</span>
                    <span className="hover:text-accent transition-colors cursor-default">ENGINE: PDF_PLAYWRIGHT_V8</span>
                </div>
                <div className="ml-auto flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <span className="font-mono text-[8px] text-ivory/20">LATENCY: 124MS</span>
                        <div className="w-16 h-1 bg-white/5 rounded-full overflow-hidden">
                            <motion.div initial={{ width: "20%" }} animate={{ width: "65%" }} transition={{ repeat: Infinity, duration: 3, repeatType: "reverse" }} className="h-full bg-accent/40" />
                        </div>
                    </div>
                </div>
            </div>
            <div className="max-w-6xl mx-auto mt-12 pt-8 border-t border-warmBrown/5 flex justify-between items-center opacity-40">
                <div className="flex gap-8">
                    <div className="flex flex-col">
                        <span className="font-mono text-[8px] uppercase tracking-[0.3em]">Quantum Portfolio Engine</span>
                        <span className="font-serif italic text-[11px]">Secure Admin Core v8.2.1</span>
                    </div>
                </div>
                <span className="font-mono text-[9px] text-accent/60">© 2026 // ADMIN_CORE</span>
            </div>
            {/* Language Prompt Modal */}
            <AnimatePresence>
                {showDownloadPrompt && (
                    <div className={`fixed inset-0 z-[300] flex items-center justify-center ${isVerifyingBeforeDownload ? 'p-0' : 'p-6'}`}>
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowDownloadPrompt(false)}
                            className="absolute inset-0 bg-warmBlack/60 backdrop-blur-md"
                        />
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className={`relative bg-white border border-warmBrown/10 shadow-2xl overflow-hidden transition-all duration-500 ${isVerifyingBeforeDownload ? 'w-screen h-screen' : 'w-full max-w-md'}`}
                        >
                            {!isVerifyingBeforeDownload ? (
                                <>
                                    <div className="bg-warmBrown p-8 text-center">
                                        <Languages className="mx-auto text-accent mb-4" size={32} />
                                        <h3 className="font-serif text-2xl italic text-ivory">Document Localization</h3>
                                        <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-ivory/40 mt-2">Selection Required for {previewCountry.toUpperCase()}</p>
                                    </div>
                                    
                                    <div className="p-8 space-y-4">
                                        <p className="font-serif text-sm text-center text-warmBrown/60 leading-relaxed mb-6">
                                            This region supports specialized layouts. Select the primary language for this application package.
                                        </p>
                                        
                                        <button 
                                            onClick={handleNativeChoice}
                                            className="w-full group flex items-center justify-between p-5 border border-warmBrown/10 hover:border-accent hover:bg-accent/5 transition-all"
                                        >
                                            <div className="text-left">
                                                <div className="font-mono text-[8px] uppercase tracking-widest text-warmBrown/40 mb-1">Local Standard</div>
                                                <div className="font-serif text-lg italic text-warmBrown group-hover:text-accent">
                                                    {previewCountry === 'japan' ? '日本語 (Japanese)' : previewCountry === 'korea' ? '한국어 (Korean)' : '简体中文 (Chinese)'}
                                                </div>
                                            </div>
                                            <Eye size={16} className="text-warmBrown/10 group-hover:text-accent" />
                                        </button>

                                        <button 
                                            onClick={() => triggerDownload('en')}
                                            className="w-full group flex items-center justify-between p-5 border border-warmBrown/10 hover:border-accent hover:bg-accent/5 transition-all"
                                        >
                                            <div className="text-left">
                                                <div className="font-mono text-[8px] uppercase tracking-widest text-warmBrown/40 mb-1">Global Standard</div>
                                                <div className="font-serif text-lg italic text-warmBrown group-hover:text-accent">English (International)</div>
                                            </div>
                                            <Download size={16} className="text-warmBrown/10 group-hover:text-accent" />
                                        </button>

                                        <button 
                                            onClick={() => setShowDownloadPrompt(false)}
                                            className="w-full py-4 font-mono text-[9px] uppercase tracking-widest text-warmBrown/30 hover:text-red-500 transition-colors"
                                        >
                                            Cancel Operation
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <div className="flex h-full flex-col">
                                    <div className="bg-warmBlack p-4 flex justify-between items-center border-b border-accent/20">
                                        <div className="flex items-center gap-4">
                                            <div className="p-2 bg-accent/10 rounded">
                                                <ShieldCheck size={18} className="text-accent" />
                                            </div>
                                            <div>
                                                <h3 className="font-serif text-lg italic text-ivory">Verification Suite: {previewCountry.toUpperCase()}</h3>
                                                <p className="font-mono text-[8px] uppercase tracking-[0.3em] text-accent/60">Stage 2 // Real-time Neural Alignment</p>
                                            </div>
                                        </div>
                                        <div className="flex gap-4">
                                            <button 
                                                onClick={() => setIsVerifyingBeforeDownload(false)}
                                                className="px-4 py-2 font-mono text-[10px] uppercase tracking-widest text-ivory/40 hover:text-white transition-all"
                                            >
                                                Back
                                            </button>
                                            <button 
                                                onClick={() => triggerDownload(verificationLang)}
                                                className="px-8 py-2 bg-accent text-white font-mono text-[10px] uppercase tracking-[0.25em] hover:bg-white hover:text-black transition-all flex items-center gap-2"
                                            >
                                                <Download size={14} /> Confirm & Download PDF
                                            </button>
                                        </div>
                                    </div>

                                    <div className="flex-1 flex overflow-hidden">
                                        {/* Dual Resume Preview (Comparison) */}
                                        <div className="w-[65%] h-full bg-ivory/5 p-4 overflow-hidden flex flex-col border-r border-warmBrown/10">
                                            <div className="flex justify-between items-center mb-4">
                                                <div className="flex items-center gap-4">
                                                    <span className="font-mono text-[9px] text-warmBrown/40 uppercase tracking-widest flex items-center gap-2">
                                                        <Maximize2 size={10} /> Comparative Analysis
                                                    </span>
                                                    <div className="h-3 w-px bg-warmBrown/10" />
                                                    <span className="font-mono text-[9px] text-accent font-bold uppercase">EN vs {verificationLang.toUpperCase()}</span>
                                                </div>
                                                <button onClick={() => {
                                                    const iframe1 = document.getElementById('verification-iframe-en');
                                                    const iframe2 = document.getElementById('verification-iframe-target');
                                                    if (iframe1) iframe1.src = iframe1.src;
                                                    if (iframe2) iframe2.src = iframe2.src;
                                                }} className="text-accent hover:rotate-180 transition-all duration-500 flex items-center gap-2 font-mono text-[8px] uppercase tracking-widest">
                                                    <RefreshCw size={12} /> Sync Both signals
                                                </button>
                                            </div>
                                            
                                            <div className="flex-1 flex gap-4 overflow-hidden">
                                                {/* English Reference */}
                                                <div className="flex-1 flex flex-col h-full opacity-60 hover:opacity-100 transition-opacity">
                                                    <div className="bg-warmBrown/5 px-3 py-1 border border-warmBrown/10 border-b-0 rounded-t flex justify-between items-center">
                                                        <span className="font-mono text-[7px] uppercase tracking-widest text-warmBrown/40">Reference (EN)</span>
                                                        <div className="flex gap-1">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-warmBrown/20" />
                                                            <div className="w-1.5 h-1.5 rounded-full bg-warmBrown/20" />
                                                        </div>
                                                    </div>
                                                    <iframe 
                                                        id="verification-iframe-en"
                                                        src={`http://localhost:8000/api/resume/preview/${previewCountry}?lang=en&cover=${includeCoverLetter}&v=${Date.now()}`}
                                                        className="flex-1 w-full border border-warmBrown/10 bg-white shadow-sm"
                                                    />
                                                </div>

                                                {/* Target Translation */}
                                                <div className="flex-1 flex flex-col h-full">
                                                    <div className="bg-accent/5 px-3 py-1 border border-accent/20 border-b-0 rounded-t flex justify-between items-center">
                                                        <span className="font-mono text-[7px] uppercase tracking-widest text-accent/60">Live Signal ({verificationLang.toUpperCase()})</span>
                                                        <div className="flex gap-1">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-accent/40 animate-pulse" />
                                                            <div className="w-1.5 h-1.5 rounded-full bg-accent/40" />
                                                        </div>
                                                    </div>
                                                    <iframe 
                                                        id="verification-iframe-target"
                                                        src={`http://localhost:8000/api/resume/preview/${previewCountry}?lang=${verificationLang}&cover=${includeCoverLetter}&v=${Date.now()}`}
                                                        className="flex-1 w-full border border-accent/20 bg-white shadow-md ring-1 ring-accent/5"
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        {/* Translation Editor */}
                                        <div className="w-[35%] h-full bg-white overflow-y-auto p-6 custom-scrollbar">
                                            <div className="flex justify-between items-center mb-8 pb-4 border-b border-warmBrown/5">
                                                <h4 className="font-serif text-xl italic">Neural Alignment (Strings)</h4>
                                                <span className="font-mono text-[10px] bg-accent/10 text-accent px-2 py-1 uppercase">{verificationLang} Registry</span>
                                            </div>
                                            
                                            <div className="space-y-6">
                                                {translations.filter(t => t.locale === verificationLang).length === 0 && (
                                                    <div className="py-20 text-center border border-dashed border-warmBrown/10 rounded-xl">
                                                        <Info className="mx-auto text-warmBrown/20 mb-3" />
                                                        <p className="font-mono text-[10px] text-warmBrown/30 uppercase tracking-widest">No strings detected for this region yet.</p>
                                                    </div>
                                                )}
                                                {translations.filter(t => t.locale === verificationLang).map(t => (
                                                    <div key={t.id} className={`p-5 border transition-all ${t.is_verified ? 'border-accent/30 bg-accent/5' : 'border-warmBrown/10'}`}>
                                                        <div className="flex justify-between items-center mb-3">
                                                            <span className="font-mono text-[8px] uppercase tracking-widest text-warmBrown/40">{t.field_name}</span>
                                                            {t.is_verified && <span className="font-mono text-[7px] text-accent uppercase font-bold">Verified</span>}
                                                        </div>
                                                        <textarea 
                                                            className="w-full bg-transparent border-none focus:ring-0 font-serif text-sm p-0 mb-4 h-auto min-h-[60px] resize-none"
                                                            value={t.translated_text}
                                                            onChange={(e) => {
                                                                const updated = [...translations];
                                                                const idx = updated.findIndex(item => item.id === t.id);
                                                                updated[idx].translated_text = e.target.value;
                                                                setTranslations(updated);
                                                            }}
                                                        />
                                                        <div className="flex justify-end gap-3">
                                                            <button 
                                                                onClick={() => updateTranslation(t.id, t.translated_text, true)}
                                                                className="px-3 py-1 bg-warmBlack text-ivory font-mono text-[8px] uppercase tracking-widest hover:bg-accent transition-all"
                                                            >
                                                                Update Signal
                                                            </button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Admin;
