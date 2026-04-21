import React, { useContext, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';
import { GithubIcon, LinkedinIcon, Download } from 'lucide-react';
import { useTypewriter } from '../hooks/useTypewriter';
import HeroCanvas from './HeroCanvas';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.2 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 1.2, ease: [0.33, 1, 0.68, 1] }
  }
};

const Hero = () => {
  const { data } = useContext(PortfolioContext);
  const titles = data?.profile?.titles || ["Python Software Engineer", "AI/ML Engineer", "Backend Developer", "Deep Learning Engineer"];
  const typewriterText = useTypewriter(titles);

  const downloadUrl = `http://localhost:8000/api/resume/download?download=true`;

  if (!data) return <div className="min-h-[80vh] flex items-center justify-center">Loading...</div>;
  const { profile } = data;


  return (
    <section className="min-h-screen flex flex-col pt-[20vh] relative overflow-hidden bg-background px-6" id="hero">
      {/* Structural Editorial Lines - Removed to avoid visual collisions */}

      {/* 3D Background */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none">
        {data.settings?.hero3d !== false && <HeroCanvas />}
      </div>

      <motion.div
        className="max-w-5xl mx-auto relative z-10 w-full"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div variants={itemVariants} className="mb-10">
          <div className="flex items-center gap-4">
            <span className="w-12 h-px bg-textPrimary/10"></span>
            <div className="flex items-center gap-3 bg-emerald-500/5 px-4 py-1.5 border border-emerald-500/10">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <p className="font-mono text-emerald-700/80 uppercase tracking-[0.3em] text-[10px] font-medium">
                Active: {data.experience?.find(e => e.endDate === "Present")?.role || "Synthesizing Systems"}
              </p>
            </div>
          </div>
        </motion.div>

        <h1 className="text-[12vw] md:text-[8vw] font-serif font-medium text-textPrimary leading-[1] tracking-tighter mb-8 italic">
          {profile.name}
        </h1>

        <div className="grid md:grid-cols-2 gap-12 items-baseline border-t border-textPrimary/5 pt-12">
          <motion.div variants={itemVariants} className="flex flex-col gap-6">
            <div className="w-24 h-px bg-accent/30" />
            <h2 className="text-3xl md:text-5xl font-serif text-textPrimary leading-tight min-h-[3.6rem] md:min-h-[6rem]">
              - {typewriterText}
              <span className="animate-pulse ml-1 inline-block w-[2px] h-[0.8em] bg-accent align-middle">|</span>
            </h2>
          </motion.div>

          <motion.div variants={itemVariants} className="flex flex-col gap-8">
            <div className="w-full h-px bg-textPrimary/5" />
            {/* <p className="text-xl md:text-2xl font-sans text-textPrimary opacity-80 leading-relaxed font-light">
               {profile.bio}
            </p> */}

            <div className="flex flex-col lg:flex-row lg:items-center gap-8 pt-4 w-full">
              <a href="#projects" className="group flex items-center gap-4 font-mono text-xs uppercase tracking-[0.2em] text-textPrimary whitespace-nowrap">
                <span className="w-12 h-px bg-textPrimary transition-all duration-500"></span>
                Explore Work
              </a>

                <div className="flex items-center gap-4">
                  {(data.connections || [])
                    .filter(c => c.visible !== false && c.platform !== 'Email')
                    .slice(0, 4) // Show top 4 signals in Hero
                    .map((conn, idx) => {
                      const Icon = {
                        'github': GithubIcon,
                        'linkedin': LinkedinIcon,
                        'youtube': (props) => (
                          <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-youtube">
                            <path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 2-2h15a2 2 0 0 1 2 2 24.12 24.12 0 0 1 0 10 2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2Z"/><path d="m10 15 5-3-5-3z"/>
                          </svg>
                        ),
                        'instagram': (props) => (
                          <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-instagram">
                            <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" x2="17.51" y1="6.5" y2="6.51"/>
                          </svg>
                        )
                      }[conn.platform.toLowerCase()] || GithubIcon; // Fallback to Github icon or similar

                      return (
                        <a 
                          key={idx} 
                          href={conn.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          title={conn.platform}
                          className="text-textPrimary/60 hover:text-textPrimary transition-all duration-300 hover:-translate-y-1"
                        >
                          <Icon size={18} />
                        </a>
                      );
                    })}
                </div>
                {/* Auto-Detecting Resume Download */}
                  <a
                    href={downloadUrl}
                    className="flex items-center gap-4 bg-textPrimary text-white px-8 py-5 hover:bg-accent transition-all duration-500 group whitespace-nowrap"
                  >
                    <Download size={16} />
                    <span className="font-mono text-xs uppercase tracking-[0.2em]">Resume</span>
                  </a>
              </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Signature Bobbing Anchor - Removed to prevent collisions with UI elements */}
    </section>
  );
};

export default Hero;
