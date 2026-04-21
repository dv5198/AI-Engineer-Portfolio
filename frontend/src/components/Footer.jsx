import React, { useContext } from 'react';
import { PortfolioContext } from '../context/PortfolioContext';
import { Github, Linkedin, Mail, Youtube, Instagram, MessageCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const Footer = () => {
  const { data } = useContext(PortfolioContext);
  const connections = data?.connections || [];

  const getIcon = (platform) => {
    switch (platform.toLowerCase()) {
      case 'github': return <Github size={16} />;
      case 'linkedin': return <Linkedin size={16} />;
      case 'youtube': return <Youtube size={16} />;
      case 'instagram': return <Instagram size={16} />;
      case 'email': return <Mail size={16} />;
      default: return <MessageCircle size={16} />;
    }
  };

  const getSafeUrl = (url) => {
    if (!url) return '#';
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('mailto:')) return url;
    return `https://${url}`;
  };

  const visibleConnections = connections.filter(c => c.visible !== false && c.platform.toLowerCase() !== 'email');

  return (
    <footer className="py-16 px-6 bg-contactBg text-background relative z-10 border-t border-background/5">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-10">

        <div className="flex flex-col gap-4 order-2 md:order-1 items-center md:items-start">
          <p className="font-mono text-[9px] uppercase tracking-widest text-background/40">
            &copy; {new Date().getFullYear()} Divya Nirankari. All Rights Reserved.
          </p>
          <div className="flex items-center gap-6">
            {visibleConnections.map((conn, idx) => (
              <motion.a
                key={idx}
                href={getSafeUrl(conn.url)}
                target="_blank"
                rel="noopener noreferrer"
                title={conn.platform}
                className="text-background/30 hover:text-background transition-all duration-300"
                whileHover={{ y: -2, scale: 1.1 }}
              >
                {getIcon(conn.platform)}
              </motion.a>
            ))}
          </div>
        </div>

        <div className="text-center md:text-right order-1 md:order-2 space-y-2">
          <p className="font-serif italic text-xl text-background/60">
            Software Engineer & AI Research Advocate
          </p>
          <p className="font-mono text-[8px] uppercase tracking-[0.4em] text-background/20">
            Synthesizing Intelligence // Building Tomorrow

          </p>
        </div>

      </div>
    </footer>
  );
};

export default Footer;
