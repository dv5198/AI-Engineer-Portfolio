import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

import LanguageSkills from './LanguageSkills';

const About = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.about) return null;

  const { about, stats } = data;

  const statEntries = [
    { label: "Systems Built", value: stats.projects_count },
    { label: "Engineering", value: `${stats.years_experience} Yrs` },
    { label: "ML Layers", value: stats.ml_models },
    { label: "Signature", value: stats.fun_stat }
  ];

  return (
    <section id="about" className="pt-32 pb-12 px-6 bg-background relative overflow-hidden">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-20 items-center">
        
        {/* Left Column: Text */}
        <div className="flex-[1.2] space-y-10">
          <div className="space-y-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40">Philosophy // 01</p>
            <h2 className="text-6xl md:text-7xl font-serif text-textPrimary italic leading-tight">Focus & Impact</h2>
          </div>
          
          <div className="space-y-6">
            {about.map((para, idx) => (
              <p key={idx} className="text-2xl font-sans text-textPrimary/80 leading-relaxed font-light">
                {para}
              </p>
            ))}
          </div>
        </div>

        {/* Right Column: Levitating Stats */}
        <div className="flex-1 grid grid-cols-2 gap-8 w-full relative">
          {statEntries.map((stat, idx) => (
            <motion.div
              key={idx}
              className="bg-white/50 backdrop-blur-sm border border-textPrimary/5 p-10 flex flex-col items-center justify-center shadow-none hover:shadow-2xl transition-all duration-700"
              animate={{ y: [0, -15, 0] }}
              transition={{
                duration: 5 + (idx * 1.2),
                repeat: Infinity,
                delay: idx * 0.4,
                ease: "easeInOut"
              }}
            >
              <span className="text-4xl font-serif text-textPrimary mb-3 tracking-tighter">
                {stat.value}
              </span>
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-textPrimary/40 text-center">
                {stat.label}
              </span>
            </motion.div>
          ))}
          
          <div className="col-span-2">
            <LanguageSkills />
          </div>
          
          {/* Abstract background element */}
          <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full border border-textPrimary/5 rounded-full pointer-events-none" />
        </div>
        
      </div>
    </section>
  );
};

export default About;
