import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Skills = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.skills) return null;

  const { skills } = data;

  return (
    <section id="skills" className="py-32 bg-skillsBg px-6 relative overflow-hidden">
      <div className="max-w-6xl mx-auto flex flex-col items-center">
        <div className="mb-20 text-center">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-4">Toolkit // System</p>
          <h2 className="text-5xl md:text-7xl font-serif text-textPrimary italic">Core Competencies</h2>
        </div>

        <div className="flex flex-wrap justify-center gap-6 max-w-4xl">
          {skills.map((skill, idx) => (
            <motion.div
              key={idx}
              className="px-8 py-3 bg-white/60 backdrop-blur-sm border border-textPrimary/5 rounded-full flex items-center gap-3 transition-colors duration-500 hover:bg-textPrimary group shadow-none hover:shadow-xl"
              animate={{ y: [0, -12, 0] }}
              transition={{
                duration: 4 + (idx % 4) * 1.2,
                repeat: Infinity,
                delay: idx * 0.1,
                ease: "easeInOut"
              }}
            >
              <div className="w-1.5 h-1.5 rounded-full bg-textPrimary/30 group-hover:bg-background transition-colors" />
              <span className="font-mono text-xs uppercase tracking-widest text-textPrimary group-hover:text-background transition-colors">
                {skill}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
      
      {/* Decorative background circle */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border border-textPrimary/5 rounded-full pointer-events-none -z-1" />
    </section>
  );
};

export default Skills;
