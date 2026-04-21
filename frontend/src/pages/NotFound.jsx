import React from 'react';
import { motion } from 'framer-motion';
import { Home, Compass } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-ivory text-warmBrown flex flex-col items-center justify-center relative overflow-hidden px-6">
      
      {/* Background decoration */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[100px] -z-10 mix-blend-multiply pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-warmBrown/5 rounded-full blur-[120px] -z-10 mix-blend-multiply pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="text-center relative z-20"
      >
        <h1 className="text-[150px] md:text-[250px] font-serif italic text-warmBrown/10 leading-none select-none">
          404
        </h1>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="space-y-6 pointer-events-auto">
            <h2 className="text-3xl md:text-5xl font-serif text-warmBlack">
              Trajectory <span className="italic">Lost</span>
            </h2>
            <p className="font-mono text-xs md:text-sm uppercase tracking-widest text-warmBrown/60 max-w-md mx-auto px-4">
              The coordinates you requested do not exist in this sector.
            </p>
            
            <button 
              onClick={() => navigate('/')}
              className="mt-8 px-8 py-4 border border-warmBrown/20 flex items-center gap-3 mx-auto hover:bg-warmBrown hover:text-ivory transition-all duration-500 group bg-ivory/50 backdrop-blur-sm"
            >
              <Compass size={16} className="text-accent group-hover:text-ivory transition-colors" />
              <span className="font-mono text-[10px] uppercase tracking-[0.3em] font-bold">Recalibrate Home</span>
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default NotFound;
