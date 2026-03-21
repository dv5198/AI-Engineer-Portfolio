import React, { useContext, useEffect, useState } from 'react';
import { PortfolioContext } from '../context/PortfolioContext';
import { Moon, Sun } from 'lucide-react';

const Navbar = () => {
  const { data } = useContext(PortfolioContext);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (!data) return null;

  const { sections_visibility, profile } = data;

  return (
    <nav className={`fixed top-0 w-full z-40 transition-all duration-300 ${scrolled ? 'bg-[#faf7f0]/80 backdrop-blur-[14px] py-4 shadow-sm border-b border-[#1a1510]/5' : 'bg-transparent py-6'}`}>
      <div className="max-w-6xl mx-auto px-6 tablet:px-8 flex justify-between items-center">
        
        {/* Name Logo */}
        <a href="#" className="font-serif text-xl md:text-2xl font-bold tracking-tight text-textPrimary transition-colors">
          {profile?.name}
        </a>

        {/* Links */}
        <div className="hidden md:flex gap-10 items-center font-mono text-[10px] uppercase tracking-[0.2em]">
          {sections_visibility?.about && <a href="#about" className="text-textPrimary hover:text-gray-500 transition-colors duration-300">About</a>}
          {sections_visibility?.experience && <a href="#experience" className="text-textPrimary hover:text-gray-500 transition-colors duration-300">Experience</a>}
          {sections_visibility?.skills && <a href="#skills" className="text-textPrimary hover:text-gray-500 transition-colors duration-300">Skills</a>}
          {sections_visibility?.achievements && <a href="#achievements" className="text-textPrimary hover:text-gray-500 transition-colors duration-300">Achievements</a>}
          {sections_visibility?.projects && <a href="#projects" className="text-textPrimary hover:text-gray-500 transition-colors duration-300">Work</a>}
          {sections_visibility?.contact && <a href="#contact" className="text-textPrimary hover:text-gray-500 transition-colors duration-300">Contact</a>}
          
          <div className="w-px h-4 bg-gray-300 ml-2 mr-2"></div>
          
        </div>
        
        {/* Mobile placeholder (Hidden on md as per requirement, stack grids on css) */}
        <div className="md:hidden">
          <span className="font-mono text-xs opacity-50">MENU HIDDEN</span>
        </div>

      </div>
    </nav>
  );
};

export default Navbar;
