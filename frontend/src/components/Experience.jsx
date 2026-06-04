import React, { useContext, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';
import { X } from 'lucide-react';

const ExperienceItem = ({ job, idx, isModal = false }) => (
  <motion.div 
    key={idx}
      animate={!isModal ? { y: [0, -12, 0] } : {}}
      transition={!isModal ? {
        duration: 5,
        repeat: Infinity,
        delay: idx * 0.4,
        ease: "easeInOut"
      } : {}}
      className={`group relative border-l border-textPrimary/10 pl-8 ${isModal ? 'pb-8' : 'pb-12'} last:pb-0`}
    >
      {/* Timeline Dot */}
      <div className="absolute left-[-5px] top-2 w-2 h-2 rounded-full bg-textPrimary/20 group-hover:bg-accent transition-colors" />
      
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-4">
          <h3 className={`${isModal ? 'text-xl' : 'text-2xl'} font-serif text-textPrimary`}>{job.role}</h3>
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
          <li key={bIdx} className={`${isModal ? 'text-base' : 'text-lg'} font-sans text-textPrimary/70 leading-relaxed font-light flex gap-4`}>
            <span className="text-accent mt-2 w-1.5 h-1.5 rounded-full bg-accent/20 border border-accent/40 flex-shrink-0" />
            {bullet}
          </li>
        ))}
      </ul>
    </motion.div>
  );

const Experience = () => {
  const { data } = useContext(PortfolioContext);
  const [showAll, setShowAll] = useState(false);

  if (!data || !data.sections_visibility?.experience) return null;

  const visibleExperience = data.experience.filter(job => job.visible !== false);
  const latestExperience = visibleExperience.slice(0, 6);
  const hasMore = visibleExperience.length > 6;

  return (
    <section id="experience" className="pt-8 pb-16 px-6 bg-background">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-4">Journey // 02</p>
          <h2 className="text-6xl md:text-7xl font-serif text-textPrimary italic">Experience</h2>
        </div>

        <div className="space-y-12">
          {latestExperience.map((job, idx) => (
            <ExperienceItem key={idx} job={job} idx={idx} />
          ))}
        </div>

        {hasMore && (
          <div className="mt-16 flex justify-center">
            <button 
              onClick={() => setShowAll(true)}
              className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent hover:text-textPrimary transition-colors border-b border-accent/20 pb-2"
            >
              Continue to full history —
            </button>
          </div>
        )}
      </div>

      {/* Full Experience Modal */}
      <AnimatePresence>
        {showAll && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 md:p-12">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAll(false)}
              className="absolute inset-0 bg-white/80 backdrop-blur-md"
            />
            <motion.div 
              initial={{ opacity: 0, y: 50, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 50, scale: 0.95 }}
              className="bg-white border border-textPrimary/5 shadow-2xl w-full max-w-4xl max-h-full overflow-hidden flex flex-col relative z-10"
            >
              <div className="p-8 border-b border-textPrimary/5 flex justify-between items-center bg-ivory/20">
                <div>
                  <h3 className="text-3xl font-serif italic text-textPrimary">Professional Archives</h3>
                  <p className="font-mono text-[9px] uppercase tracking-widest text-textPrimary/40 mt-1">Complete Career Sequence // {visibleExperience.length} Nodes</p>
                </div>
                <button 
                  onClick={() => setShowAll(false)}
                  className="w-10 h-10 flex items-center justify-center border border-textPrimary/10 text-textPrimary/20 hover:text-accent hover:border-accent/20 transition-all"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-8 md:p-12 custom-scrollbar">
                <div className="space-y-16">
                  {visibleExperience.map((job, idx) => (
                    <ExperienceItem key={idx} job={job} idx={idx} isModal={true} />
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  );
};

export default Experience;

