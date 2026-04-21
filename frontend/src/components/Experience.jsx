import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Experience = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.experience) return null;

  return (
    <section id="experience" className="pt-8 pb-16 px-6 bg-background">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-4">Journey // 02</p>
          <h2 className="text-6xl md:text-7xl font-serif text-textPrimary italic">Experience</h2>
        </div>

        <div className="space-y-12">
          {data.experience.filter(job => job.visible !== false).map((job, idx) => (
            <motion.div 
              key={idx}
              animate={{ y: [0, -12, 0] }}
              transition={{
                duration: 5,
                repeat: Infinity,
                delay: idx * 0.4,
                ease: "easeInOut"
              }}
              className="group relative border-l border-textPrimary/10 pl-8 pb-12 last:pb-0"
            >
              {/* Timeline Dot */}
              <div className="absolute left-[-5px] top-2 w-2 h-2 rounded-full bg-textPrimary/20 group-hover:bg-accent transition-colors" />
              
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div className="flex items-center gap-4">
                  <h3 className="text-2xl font-serif text-textPrimary">{job.role}</h3>
                  {job.endDate === "Present" && (
                    <span className="bg-emerald-600 text-white text-[9px] font-mono px-3 py-1 rounded-sm uppercase tracking-widest shadow-lg shadow-emerald-500/20">
                      Currently Active
                    </span>
                  )}
                </div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-textPrimary/40">
                  {job.startDate} — {job.endDate}
                </span>
              </div>

              <div className="mb-6">
                <span className="font-mono text-xs uppercase tracking-widest text-accent">{job.company}</span>
                <span className="text-textPrimary/30 mx-3">/</span>
                <span className="font-mono text-xs uppercase tracking-widest text-textPrimary/40">{job.location}</span>
              </div>

              <ul className="space-y-4 max-w-3xl">
                {job.bullets?.map((bullet, bIdx) => (
                  <li key={bIdx} className="text-lg font-sans text-textPrimary/70 leading-relaxed font-light flex gap-4">
                    <span className="text-accent mt-2 w-1.5 h-1.5 rounded-full bg-accent/20 border border-accent/40 flex-shrink-0" />
                    {bullet}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Experience;
