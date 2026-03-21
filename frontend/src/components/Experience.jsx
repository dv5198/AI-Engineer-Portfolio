import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Experience = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.experience || !data.experience) return null;

  return (
    <section id="experience" className="py-32 px-6 bg-[#faf7f0]">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-4">Chronicle // 02</p>
          <h2 className="text-6xl md:text-7xl font-serif text-textPrimary italic">Experience</h2>
        </div>

        <div className="space-y-12">
          {data.experience.map((job, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              className="group relative border-l border-textPrimary/10 pl-8 pb-12 last:pb-0"
            >
              {/* Timeline Dot */}
              <div className="absolute left-[-5px] top-2 w-2 h-2 rounded-full bg-textPrimary/20 group-hover:bg-accent transition-colors" />
              
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div className="flex items-center gap-4">
                  <h3 className="text-2xl font-serif text-textPrimary">{job.position}</h3>
                  {job.end === "Present" && (
                    <span className="bg-green-600 text-white text-[10px] font-mono px-2 py-0.5 rounded uppercase tracking-wider">
                      Currently Active
                    </span>
                  )}
                </div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-textPrimary/40">
                  {job.start} — {job.end}
                </span>
              </div>

              <div className="mb-4">
                <span className="font-mono text-xs uppercase tracking-widest text-accent">{job.company}</span>
                <span className="text-textPrimary/30 mx-3">/</span>
                <span className="font-mono text-xs uppercase tracking-widest text-textPrimary/40">{job.location}</span>
              </div>

              <p className="text-lg font-sans text-textPrimary/70 max-w-3xl leading-relaxed font-light">
                {job.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Experience;
