import React, { useEffect, useState } from 'react';
import { Mail, User, Clock, Trash2, Reply, CheckCircle, Circle } from 'lucide-react';

const MessageInbox = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchMessages = () => {
        setLoading(true);
        fetch('http://localhost:8001/api/platform/messages')
            .then(res => res.json())
            .then(data => {
                setMessages(data);
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchMessages();
    }, []);

    const deleteMessage = async (id) => {
        try {
            const res = await fetch(`http://localhost:8001/api/platform/messages/${id}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                setMessages(messages.filter(msg => msg.id !== id));
            }
        } catch (err) {
            console.error('Delete failed', err);
        }
    };

    const toggleRead = async (id) => {
        try {
            const res = await fetch(`http://localhost:8001/api/platform/messages/${id}/toggle-read`, {
                method: 'POST'
            });
            if (res.ok) {
                const result = await res.json();
                setMessages(messages.map(msg => 
                    msg.id === id ? { ...msg, read: result.read } : msg
                ));
            }
        } catch (err) {
            console.error('Toggle read failed', err);
        }
    };

    const handleReply = (msg) => {
        const mailto = `mailto:${msg.email}?subject=Re: ${encodeURIComponent(msg.subject)}&body=${encodeURIComponent(`\n\n--- Original Message ---\nFrom: ${msg.name}\nDate: ${new Date(msg.timestamp).toLocaleString()}\n\n${msg.message}`)}`;
        window.location.href = mailto;
    };

    if (loading && messages.length === 0) return <div className="py-20 text-center font-mono text-[10px] text-warmBrown/40">Opening secure channel...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end border-b border-warmBrown/5 pb-4">
                <h3 className="font-serif text-xl">Inbound Transmissions</h3>
                <span className="font-mono text-[10px] text-warmBrown/30 uppercase tracking-widest">
                    {messages.filter(m => !m.read).length} Unseen // {messages.length} Total
                </span>
            </div>
            
            <div className="space-y-4">
                {messages.map((msg, i) => (
                    <div key={msg.id || i} className={`bg-white border p-8 shadow-sm group transition-all duration-500 ${!msg.read ? 'border-accent/20 border-l-4 border-l-accent' : 'border-warmBrown/5'}`}>
                        <div className="flex justify-between items-start mb-6">
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 flex items-center justify-center transition-colors ${!msg.read ? 'bg-accent text-white' : 'bg-ivory-deep/30 text-warmBrown/40'}`}>
                                    <User size={18} />
                                </div>
                                <div>
                                    <div className="flex items-center gap-3">
                                        <h4 className="font-serif text-lg text-warmBrown leading-none">{msg.name}</h4>
                                        {!msg.read && <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />}
                                    </div>
                                    <p className="font-mono text-[10px] text-warmBrown/40 mt-1">{msg.email}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="flex items-center gap-2 text-warmBrown/20 font-mono text-[9px] mb-2 uppercase">
                                    <Clock size={10} />
                                    {new Date(msg.timestamp).toLocaleString()}
                                </div>
                                <div className="flex gap-4 justify-end opacity-0 group-hover:opacity-100 transition-all font-mono">
                                    <button 
                                        onClick={() => toggleRead(msg.id)} 
                                        className={`transition-colors ${msg.read ? 'text-warmBrown/20 hover:text-warmBrown' : 'text-accent hover:text-accent-dark'}`}
                                        title={msg.read ? "Mark as Unread" : "Mark as Read"}
                                    >
                                        {msg.read ? <Circle size={14} /> : <CheckCircle size={14} />}
                                    </button>
                                    <button 
                                        onClick={() => handleReply(msg)} 
                                        className="text-warmBrown/20 hover:text-accent transition-colors"
                                        title="Reply via Email"
                                    >
                                        <Reply size={14} />
                                    </button>
                                    <button 
                                        onClick={() => deleteMessage(msg.id)} 
                                        className="text-warmBrown/20 hover:text-red-500 transition-colors"
                                        title="Archive (Delete)"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div className={`p-6 border-l-2 transition-all duration-500 ${!msg.read ? 'bg-accent/5 border-accent' : 'bg-ivory/20 border-accent/20'}`}>
                            <h5 className="font-mono text-[10px] uppercase tracking-widest text-accent mb-3">{msg.subject || 'No Subject'}</h5>
                            <p className="text-sm font-sans text-warmBrown/80 whitespace-pre-wrap leading-relaxed italic">
                                "{msg.message}"
                            </p>
                        </div>
                    </div>
                ))}

                {messages.length === 0 && (
                     <div className="py-24 text-center border border-dashed border-warmBrown/10 font-mono text-[10px] text-warmBrown/30 uppercase tracking-[0.4em] bg-white/50">
                        Signal Silence
                    </div>
                )}
            </div>
        </div>
    );
};

export default MessageInbox;

