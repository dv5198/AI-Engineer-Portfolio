import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const LanguageSkills = () => {
  const { data } = useContext(PortfolioContext);
  const languages = data?.languages?.filter(l => l.visible !== false) || [];

  const getLevelPercentage = (level) => {
    const l = level?.toLowerCase() || '';
    if (l.includes('native') || l.includes('fluent')) return 100;
    if (l.includes('business') || l.includes('professional')) return 90;
    if (l.includes('advanced')) return 80;
    if (l.includes('intermediate')) return 60;
    if (l.includes('basic') || l.includes('elementary')) return 40;
    return 75; // Default fallback
  };

  if (languages.length === 0) return null;

  return (
    <div className="mt-12 space-y-6">
      <h4 className="font-mono text-[10px] uppercase tracking-[0.3em] text-warmBrown/40 mb-6 italic">Communication //</h4>
      <div className="space-y-6">
        {languages.sort((a,b) => (a.order || 0) - (b.order || 0)).map((lang, idx) => (
          <div key={lang.id || idx} className="space-y-2">
            <div className="flex justify-between items-end">
              <span className="font-mono text-xs text-warmBrown tracking-widest uppercase">{lang.name}</span>
              <span className="font-mono text-[9px] text-accent uppercase tracking-tighter">{lang.level}</span>
            </div>
            <div className="h-[2px] w-full bg-ivory-deep/30 relative overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                whileInView={{ width: `${lang.percentage || getLevelPercentage(lang.level)}%` }}
                viewport={{ once: true }}
                transition={{ duration: 1.5, delay: idx * 0.2, ease: "easeOut" }}
                className="absolute h-full bg-accent"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LanguageSkills;
