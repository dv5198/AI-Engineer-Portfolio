import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Skills = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.skills) return null;

  const { skills } = data;

  return (
    <section id="skills" className="py-16 bg-skillsBg px-6 relative overflow-hidden">
      <div className="max-w-6xl mx-auto flex flex-col items-center">
        <div className="mb-20 text-center">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-4">Toolkit // System</p>
          <h2 className="text-5xl md:text-7xl font-serif text-textPrimary italic">Core Competencies</h2>
        </div>

        <div className="w-full max-w-5xl space-y-20">
          {(data.skillCategories || []).filter(cat => cat.visible !== false).sort((a,b) => a.order - b.order).map((category, catIdx) => (
            <div key={catIdx} className="space-y-8">
              <div className="flex items-center gap-6">
                <span className="font-mono text-[10px] text-accent/40">{catIdx.toString().padStart(2, '0')}</span>
                <h3 className="text-2xl font-serif text-textPrimary italic">{category.label}</h3>
                <div className="h-[1px] flex-grow bg-textPrimary/5" />
              </div>
              
              <div className="flex flex-wrap gap-4">
                {(Array.isArray(category.items) ? category.items : (category.items || "").split(',').map(s => s.trim())).map((skill, idx) => (
                  <motion.div
                    key={idx}
                    className="px-6 py-2 bg-white/40 backdrop-blur-md border border-textPrimary/5 rounded-full flex items-center gap-3 transition-all duration-500 hover:bg-textPrimary group shadow-sm hover:shadow-xl"
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{
                      duration: 0.5,
                      delay: (catIdx * 0.2) + (idx * 0.05)
                    }}
                  >
                    <div className="w-1 h-1 rounded-full bg-accent group-hover:bg-background transition-colors" />
                    <span className="font-mono text-[10px] uppercase tracking-widest text-textPrimary group-hover:text-background transition-colors">
                      {skill}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Decorative background circle */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border border-textPrimary/5 rounded-full pointer-events-none -z-1" />
    </section>
  );
};

export default Skills;
