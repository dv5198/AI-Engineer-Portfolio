import React, { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

const CustomCursor = () => {
  const [isHovering, setIsHovering] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  
  const mouseX = useMotionValue(-100);
  const mouseY = useMotionValue(-100);

  const ringX = useSpring(mouseX, { stiffness: 150, damping: 15, mass: 0.5 });
  const ringY = useSpring(mouseY, { stiffness: 150, damping: 15, mass: 0.5 });

  useEffect(() => {
    const moveCursor = (e) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
      if (!isVisible) setIsVisible(true);
    };

    const handleMouseOver = (e) => {
      const isInteractive = e.target.tagName.toLowerCase() === 'a' || 
                            e.target.tagName.toLowerCase() === 'button' || 
                            e.target.closest('a') || 
                            e.target.closest('button');
      setIsHovering(!!isInteractive);
    };

    window.addEventListener('mousemove', moveCursor);
    window.addEventListener('mouseover', handleMouseOver);

    return () => {
      window.removeEventListener('mousemove', moveCursor);
      window.removeEventListener('mouseover', handleMouseOver);
    };
  }, [mouseX, mouseY, isVisible]);

  // Check cursor device roughly
  if (typeof window !== 'undefined' && window.matchMedia("(pointer: coarse)").matches) return null;

  return (
    <div className={`pointer-events-none z-[100] fixed inset-0 ${!isVisible ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}>
      {/* 8px solid dot */}
      <motion.div
        className="absolute top-0 left-0 w-2 h-2 rounded-full bg-textPrimary pointer-events-none mix-blend-difference"
        style={{ x: mouseX, y: mouseY, translateX: '-50%', translateY: '-50%' }}
      />
      {/* 32px ring border */}
      <motion.div
        className="absolute top-0 left-0 w-8 h-8 rounded-full border border-textPrimary pointer-events-none mix-blend-difference"
        style={{ x: ringX, y: ringY, translateX: '-50%', translateY: '-50%' }}
        animate={{ 
          scale: isHovering ? 1.5 : 1, 
          opacity: isHovering ? 0.3 : 0.8 
        }}
        transition={{ duration: 0.15 }}
      />
    </div>
  );
};

export default CustomCursor;
