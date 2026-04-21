import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const ContactForm = () => {
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' });
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [errorMsg, setErrorMsg] = useState('');

  const validate = () => {
    if (!formData.name || !formData.email || !formData.message) return "Please fill all required fields.";
    if (!/\S+@\S+\.\S+/.test(formData.email)) return "Please enter a valid email address.";
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const error = validate();
    if (error) {
      setErrorMsg(error);
      setStatus('error');
      return;
    }

    setStatus('loading');
    try {
      const res = await fetch('http://localhost:8000/api/platform/contact/send/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        setStatus('success');
        setFormData({ name: '', email: '', subject: '', message: '' });
      } else {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to send');
      }
    } catch (err) {
      setErrorMsg(err.message);
      setStatus('error');
    }
  };

  return (
    <div className="bg-white/40 backdrop-blur-md border border-warmBrown/5 p-8 md:p-12 shadow-sm">
      <AnimatePresence mode="wait">
        {status === 'success' ? (
          <motion.div
            key="success"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="h-full flex flex-col items-center justify-center py-12 text-center"
          >
            <span className="text-4xl mb-6 text-accent italic">✓</span>
            <h3 className="text-3xl font-serif text-warmBrown italic mb-4">Message Transmitted</h3>
            <p className="font-sans text-warmBrown/60 leading-relaxed max-w-xs">
              Thank you for reaching out. I'll get back to you across the signals soon.
            </p>
            <button 
              onClick={() => setStatus('idle')}
              className="mt-8 font-mono text-[10px] text-accent uppercase tracking-widest hover:underline"
            >
              Send another?
            </button>
          </motion.div>
        ) : (
          <motion.form
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onSubmit={handleSubmit}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="block font-mono text-[9px] uppercase tracking-widest text-warmBrown/40 px-1">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="Your Name"
                  className="w-full bg-transparent border-b border-warmBrown/10 py-3 px-1 focus:outline-none focus:border-accent font-serif placeholder:text-warmBrown/20 transition-colors"
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="block font-mono text-[9px] uppercase tracking-widest text-warmBrown/40 px-1">Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="you@domain.com"
                  className="w-full bg-transparent border-b border-warmBrown/10 py-3 px-1 focus:outline-none focus:border-accent font-serif placeholder:text-warmBrown/20 transition-colors"
                  onChange={e => setFormData({...formData, email: e.target.value.replace(/\s+/g, '')})}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block font-mono text-[9px] uppercase tracking-widest text-warmBrown/40 px-1">Subject</label>
              <input
                type="text"
                placeholder="Regarding project..."
                className="w-full bg-transparent border-b border-warmBrown/10 py-3 px-1 focus:outline-none focus:border-accent font-serif placeholder:text-warmBrown/20 transition-colors"
                value={formData.subject}
                onChange={e => setFormData({...formData, subject: e.target.value})}
              />
            </div>

            <div className="space-y-2">
              <label className="block font-mono text-[9px] uppercase tracking-widest text-warmBrown/40 px-1">Message *</label>
              <textarea
                required
                rows={5}
                placeholder="What's on your mind?"
                className="w-full bg-transparent border-b border-warmBrown/10 py-3 px-1 focus:outline-none focus:border-accent font-serif placeholder:text-warmBrown/20 transition-colors resize-none"
                value={formData.message}
                onChange={e => setFormData({...formData, message: e.target.value})}
              />
            </div>

            {status === 'error' && (
              <p className="text-[10px] font-mono text-red-400 mt-4 uppercase tracking-tighter">
                Error: {errorMsg}
              </p>
            )}

            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full bg-warmBrown text-ivory py-4 font-mono text-xs uppercase tracking-[0.3em] hover:bg-accent transition-all duration-500 disabled:opacity-50"
            >
              {status === 'loading' ? 'Transmitting...' : 'Dispatch Message'}
            </button>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ContactForm;
