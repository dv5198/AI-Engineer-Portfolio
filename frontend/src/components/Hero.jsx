import React, { useContext, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';
import { DownloadIcon, GithubIcon, LinkedinIcon, ArrowUpRight } from 'lucide-react';

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
  if (!data) return <div className="min-h-[80vh] flex items-center justify-center">Loading...</div>;
  const { profile } = data;

  const handleResumeDownload = () => {
    window.location.href = 'http://localhost:8000/api/resume/download';
  };

  return (
    <section className="min-h-screen flex flex-col justify-center relative overflow-hidden bg-background px-6" id="hero">
      {/* Structural Editorial Lines */}
      <div className="absolute top-0 left-[10%] w-px h-full bg-textPrimary/5 pointer-events-none" />
      <div className="absolute top-0 left-[40%] w-px h-full bg-textPrimary/5 pointer-events-none" />
      <div className="absolute top-[30%] left-0 w-full h-px bg-textPrimary/5 pointer-events-none" />
      
      {/* Levitating Decorative Wireframe Circles */}
      <motion.div 
        className="absolute top-[15%] right-[10%] w-64 h-64 border border-textPrimary/10 rounded-full pointer-events-none hidden md:block"
        animate={{ y: [0, -20, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div 
        className="absolute bottom-[20%] left-[5%] w-32 h-32 border border-textPrimary/10 rounded-full pointer-events-none hidden md:block"
        animate={{ y: [0, -15, 0], scale: [1, 1.1, 1] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.div 
        variants={containerVariants} 
        initial="hidden" 
        animate="visible"
        className="max-w-5xl mx-auto relative z-10"
      >
        <motion.div variants={itemVariants} className="mb-10">
          <p className="font-mono text-textPrimary/60 uppercase tracking-[0.4em] text-[10px] flex items-center gap-3">
            <span className="w-8 h-px bg-textPrimary/20"></span>
            Currently Building
          </p>
        </motion.div>
        
        <motion.h1 variants={itemVariants} className="text-[12vw] md:text-[8vw] font-serif font-medium text-textPrimary leading-[1] tracking-tighter mb-8 italic">
          {profile.name}
        </motion.h1>
        
        <div className="grid md:grid-cols-2 gap-12 items-baseline">
          <motion.h2 variants={itemVariants} className="text-3xl md:text-5xl font-serif text-textPrimary leading-tight">
            {profile.role.split(' ').map((word, i) => (
              <span key={i} className={i % 2 !== 0 ? 'italic font-serif opacity-70 block md:inline' : ''}>
                {word}{' '}
              </span>
            ))}
          </motion.h2>
          
          <motion.div variants={itemVariants} className="flex flex-col gap-8">
            <p className="text-xl md:text-2xl font-sans text-textPrimary opacity-80 leading-relaxed font-light">
              {profile.bio}
            </p>

            <div className="flex flex-wrap gap-8 items-center pt-4">
              <a href="#projects" className="group flex items-center gap-4 font-mono text-xs uppercase tracking-[0.2em] text-textPrimary">
                <span className="group-hover:w-20 w-12 h-px bg-textPrimary transition-all duration-500"></span>
                Explore Work
              </a>
              
              <div className="flex gap-6 items-center">
                <a href={profile.github} target="_blank" rel="noopener noreferrer" className="text-textPrimary/60 hover:text-textPrimary transition-colors">
                  <GithubIcon size={18} />
                </a>
                <a href={profile.linkedin} target="_blank" rel="noopener noreferrer" className="text-textPrimary/60 hover:text-textPrimary transition-colors">
                  <LinkedinIcon size={18} />
                </a>
              </div>

              <button 
                onClick={handleResumeDownload}
                className="font-mono text-[10px] uppercase tracking-[0.2em] border border-textPrimary/20 px-6 py-3 hover:bg-textPrimary hover:text-background transition-all"
              >
                Get Resume
              </button>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Signature Bobbing Anchor */}
      <motion.div 
        className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-4 text-textPrimary/30"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="w-px h-24 bg-gradient-to-b from-textPrimary/40 to-transparent" />
        <span className="font-mono text-[8px] uppercase tracking-widest">Antigravity</span>
      </motion.div>
    </section>
  );
};

export default Hero;
