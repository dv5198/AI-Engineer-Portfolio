import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { Github, Linkedin, Mail, Youtube, Instagram, MessageCircle } from 'lucide-react';
import { PortfolioContext } from '../context/PortfolioContext';
import ContactForm from './ContactForm';

const Contact = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.contact) return null;

  const { profile, connections = [] } = data;

  // Icon Mapper
  // Icon Mapper
  const getIcon = (platform) => {
    switch (platform.toLowerCase()) {
      case 'github': return <Github size={20} />;
      case 'linkedin': return <Linkedin size={20} />;
      case 'youtube': return <Youtube size={20} />;
      case 'instagram': return <Instagram size={20} />;
      case 'email': return <Mail size={20} />;
      default: return <MessageCircle size={20} />; // Placeholder for KakaoTalk, Slack, etc.
    }
  };

  const getSafeUrl = (url) => {
    if (!url) return '#';
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('mailto:')) return url;
    return `https://${url}`;
  };

  const links = connections
    .filter(c => c.visible !== false)
    .filter(c => !['youtube', 'instagram'].includes(c.platform.toLowerCase()))
    .map(c => ({
      name: c.platform,
      icon: getIcon(c.platform),
      url: getSafeUrl(c.url)
    }));

  return (
    <section id="contact" className="pt-8 pb-20 bg-ivory text-warmBrown relative z-10 px-6">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-20">

        {/* Left: Info & Links */}
        <div className="space-y-16">
          <div className="space-y-8">
            <h2 className="text-6xl md:text-8xl font-serif italic leading-tight text-warmBlack">Get In<br />Touch</h2>
            <p className="font-serif italic text-2xl text-warmBrown/60 max-w-md leading-relaxed">
              Interested in the intersection of scalable systems and machine intelligence.
            </p>
          </div>

          <div className="flex flex-row flex-wrap gap-4">
            {links.map((link, idx) => (
              <motion.a
                key={idx}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex-1 flex items-center justify-between px-6 py-4 border border-warmBrown/10 hover:border-accent transition-all duration-500 min-w-[160px]"
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 4, repeat: Infinity, delay: idx * 0.2 }}
              >
                <div className="flex items-center gap-6">
                  <span className="text-accent">{link.icon}</span>
                  <span className="font-mono text-xs uppercase tracking-[0.3em] font-medium">{link.name}</span>
                </div>
                <span className="text-accent opacity-0 group-hover:opacity-100 transition-opacity">→</span>
              </motion.a>
            ))}
          </div>
        </div>

        {/* Right: Form */}
        <div>
          <ContactForm />
        </div>

      </div>
    </section>
  );
};

export default Contact;
