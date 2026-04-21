import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Achievements = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.achievements) return null;

  const { achievement_image } = data;

  return (
    <section id="achievements" className="py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20 flex flex-col md:flex-row justify-between items-end gap-8">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-4">Milestones // 03</p>
            <h2 className="text-6xl md:text-7xl font-serif text-textPrimary italic">Achievements</h2>
          </div>
        </div>

        {/* Featured Achievement Image Card */}
        {achievement_image && achievement_image.url && (
          <motion.div 
            animate={{ y: [0, -12, 0] }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="mb-20 bg-white border border-textPrimary/5 shadow-none hover:shadow-2xl transition-all duration-700 overflow-hidden"
          >
            <img 
              src={achievement_image.url} 
              alt="Featured Achievement" 
              className="w-full h-[500px] object-cover grayscale-[0.5] hover:grayscale-0 transition-all duration-1000"
            />
            {achievement_image.caption && (
              <div className="p-8 border-t border-textPrimary/5">
                <p className="font-mono text-sm tracking-widest text-textPrimary uppercase text-center">
                  {achievement_image.caption}
                </p>
              </div>
            )}
          </motion.div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {data.achievements.filter(ach => ach.visible !== false).map((achievement, idx) => (
            <motion.div 
              key={idx}
              animate={{ y: [0, -12, 0] }}
              transition={{
                duration: 5,
                repeat: Infinity,
                delay: idx * 0.4,
                ease: "easeInOut"
              }}
              className="p-10 border border-textPrimary/5 hover:border-textPrimary/20 transition-colors bg-white/50 backdrop-blur-sm"
            >
              <h3 className="text-2xl font-serif text-textPrimary mb-4">{achievement.title}</h3>
              <p className="text-lg font-sans text-textPrimary/70 leading-relaxed font-light">
                {achievement.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Achievements;
