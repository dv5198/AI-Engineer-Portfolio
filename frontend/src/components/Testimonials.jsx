import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Testimonials = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.testimonials) return null;

  const testimonials = data.testimonials?.filter(t => t.visible !== false) || [];

  return (
    <section id="testimonials" className="py-32 px-6 bg-ivory-deep/10">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-warmBrown/40 mb-4">Praise // 05</p>
          <h2 className="text-5xl md:text-6xl font-serif text-warmBrown italic">Kind Words</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
          {testimonials.map((item, idx) => (
            <motion.div
              key={item.id || idx}
              animate={{ y: [0, -12, 0] }}
              transition={{
                duration: 5 + (idx % 2),
                repeat: Infinity,
                delay: idx * 0.4,
                ease: "easeInOut"
              }}
              className="bg-white border border-warmBrown/5 p-10 relative overflow-hidden group hover:border-accent/30 transition-colors duration-500"
            >
              <span className="absolute -top-4 -left-2 text-8xl font-serif text-accent/10 pointer-events-none group-hover:text-accent/20 transition-colors duration-500">“</span>
              
              <div className="relative z-10">
                <p className="font-serif italic text-lg text-warmBrown/80 mb-8 leading-relaxed">
                  {item.quote}
                </p>
                
                <div>
                  <h4 className="font-serif font-bold text-warmBrown">{item.name}</h4>
                  <p className="font-mono text-[10px] text-warmMid uppercase tracking-widest">
                    {item.role} @ {item.company}
                  </p>
                  <p className="font-mono text-[9px] text-accent uppercase mt-1">
                    [{item.relation}]
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
