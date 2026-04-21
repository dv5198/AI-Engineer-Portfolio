import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Leaf, Check, Loader2 } from 'lucide-react';

const SubmitTestimonial = () => {
    const [formData, setFormData] = useState({
        name: '',
        role: '',
        company: '',
        relation: '',
        quote: ''
    });
    const [status, setStatus] = useState('idle'); // idle, loading, success, error
    const [errorMsg, setErrorMsg] = useState('');

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus('loading');
        try {
            const res = await fetch('http://localhost:8000/api/dynamic/testimonials/public', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            if (!res.ok) throw new Error('Submission failed');
            setStatus('success');
        } catch (err) {
            setErrorMsg(err.message);
            setStatus('error');
        }
    };

    return (
        <div className="min-h-screen bg-warmBlack flex flex-col items-center justify-center p-6 text-ivory relative overflow-hidden">
            <div className="absolute inset-0 opacity-10 pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent rounded-full mix-blend-screen filter blur-[128px]"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-textPrimary rounded-full mix-blend-screen filter blur-[128px]"></div>
            </div>

            <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-xl bg-white/5 border border-white/10 p-10 md:p-14 backdrop-blur-md relative z-10"
            >
                <div className="text-center mb-10">
                    <Leaf className="mx-auto text-accent mb-6" size={32} />
                    <h1 className="text-4xl md:text-5xl font-serif italic tracking-tight mb-2 text-ivory">Share an Experience</h1>
                    <p className="font-mono text-[10px] text-ivory/40 uppercase tracking-[0.3em]">Encrypted Storage // Pending Review</p>
                </div>

                <AnimatePresence mode="wait">
                    {status === 'success' ? (
                        <motion.div 
                            key="success"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="flex flex-col items-center justify-center py-20 text-center"
                        >
                            <div className="w-16 h-16 rounded-full border border-green-500/30 flex items-center justify-center mb-6 text-green-400">
                                <Check size={24} />
                            </div>
                            <h2 className="text-2xl font-serif italic mb-2">Artifact Deposited</h2>
                            <p className="font-mono text-xs text-ivory/50 leading-relaxed max-w-sm border-t border-ivory/10 pt-4 mt-2">
                                Your message has been successfully secured. It will be surfaced publicly upon review.
                            </p>
                            <button 
                                onClick={() => window.location.href = '/'}
                                className="mt-10 pb-1 border-b border-ivory/20 font-mono text-[10px] uppercase tracking-widest hover:text-accent hover:border-accent transition-colors"
                            >
                                Return to Surface
                            </button>
                        </motion.div>
                    ) : (
                        <motion.form 
                            key="form"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            onSubmit={handleSubmit} 
                            className="space-y-6"
                        >
                            {status === 'error' && (
                                <div className="p-4 border border-red-500/30 bg-red-500/10 text-red-300 font-mono text-[10px] uppercase tracking-widest text-center">
                                    {errorMsg}
                                </div>
                            )}
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block font-mono text-[9px] uppercase tracking-widest text-ivory/40 mb-2">Full Name</label>
                                    <input 
                                        required name="name" value={formData.name} onChange={handleChange}
                                        className="w-full bg-transparent border-b border-ivory/10 text-ivory py-3 focus:outline-none focus:border-accent font-serif placeholder:italic placeholder:text-ivory/20 transition-colors"
                                        placeholder="Jane Doe"
                                    />
                                </div>
                                <div>
                                    <label className="block font-mono text-[9px] uppercase tracking-widest text-ivory/40 mb-2">Role / Title</label>
                                    <input 
                                        required name="role" value={formData.role} onChange={handleChange}
                                        className="w-full bg-transparent border-b border-ivory/10 text-ivory py-3 focus:outline-none focus:border-accent font-serif placeholder:italic placeholder:text-ivory/20 transition-colors"
                                        placeholder="Senior Engineer"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block font-mono text-[9px] uppercase tracking-widest text-ivory/40 mb-2">Company / Organization</label>
                                    <input 
                                        required name="company" value={formData.company} onChange={handleChange}
                                        className="w-full bg-transparent border-b border-ivory/10 text-ivory py-3 focus:outline-none focus:border-accent font-serif placeholder:italic placeholder:text-ivory/20 transition-colors"
                                        placeholder="Tech Corp"
                                    />
                                </div>
                                <div>
                                    <label className="block font-mono text-[9px] uppercase tracking-widest text-ivory/40 mb-2">Relation / Context</label>
                                    <input 
                                        required name="relation" value={formData.relation} onChange={handleChange}
                                        className="w-full bg-transparent border-b border-ivory/10 text-ivory py-3 focus:outline-none focus:border-accent font-serif placeholder:italic placeholder:text-ivory/20 transition-colors"
                                        placeholder="Manager, Peer, Client"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block font-mono text-[9px] uppercase tracking-widest text-ivory/40 mb-2 flex justify-between">
                                    <span>Endorsement / Quote</span>
                                    <span className="text-ivory/20">{formData.quote.length}/500</span>
                                </label>
                                <textarea 
                                    required name="quote" value={formData.quote} onChange={handleChange} maxLength="500"
                                    className="w-full bg-ivory/5 border border-ivory/10 text-ivory p-4 focus:outline-none focus:border-accent font-serif placeholder:italic placeholder:text-ivory/20 transition-colors resize-none h-32"
                                    placeholder="Briefly describe your experience working together..."
                                />
                            </div>

                            <button 
                                type="submit" 
                                disabled={status === 'loading'}
                                className="w-full mt-8 py-5 border border-ivory/20 font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-ivory hover:text-warmBlack transition-all disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-ivory flex items-center justify-center gap-3"
                            >
                                {status === 'loading' ? (
                                    <><Loader2 size={14} className="animate-spin" /> Transmitting...</>
                                ) : 'Submit Artifact'}
                            </button>
                        </motion.form>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
};

export default SubmitTestimonial;
