import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Research = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.research) return null;

  const interests = data.researchInterests?.filter(i => i.visible !== false) || [];

  return (
    <section id="research" className="py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20 text-center">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-warmBrown/40 mb-4 italic">Next Frontier // 07</p>
          <h2 className="text-5xl md:text-6xl font-serif text-warmBrown">Research Lab</h2>
        </div>

        <div className="flex flex-wrap gap-8 justify-center">
            {interests.length > 0 ? interests.map((item, idx) => (
                <motion.div
                    key={item.id || idx}
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, ease: "easeOut", delay: idx * 0.1 }}
                    className="bg-ivory-deep/30 border border-accent/20 p-8 rounded-sm max-w-sm hover:border-accent transition-colors duration-500"
                >
                    <h3 className="text-xl font-serif italic text-warmBrown mb-2">{item.topic}</h3>
                    <p className="font-mono text-[10px] leading-relaxed text-warmMid uppercase tracking-wider">
                        {item.description}
                    </p>
                </motion.div>
            )) : (
                <p className="font-mono text-sm text-warmBrown/30 italic">Exploring new horizons...</p>
            )}
        </div>
      </div>
    </section>
  );
};

export default Research;
