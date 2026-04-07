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
    <nav className={`fixed top-0 w-full z-40 transition-all duration-300 ${scrolled ? 'bg-ivory/80 backdrop-blur-[14px] py-4 shadow-sm border-b border-warmBlack/5' : 'bg-transparent py-6'}`}>
      <div className="max-w-6xl mx-auto px-6 tablet:px-8 flex justify-between items-center text-warmBlack">
        
        {/* Name Logo */}
        <a href="#" className="font-serif text-xl md:text-2xl font-bold tracking-tight transition-colors">
          {profile?.name}
        </a>

        {/* Links */}
        <div className="hidden md:flex gap-6 items-center font-mono text-[9px] uppercase tracking-[0.2em]">
          {sections_visibility?.about && <a href="#about" className="hover:text-accent transition-colors duration-300">About</a>}
          {sections_visibility?.experience && <a href="#experience" className="hover:text-accent transition-colors duration-300">Experience</a>}
          {sections_visibility?.skills && <a href="#skills" className="hover:text-accent transition-colors duration-300">Skills</a>}
          {sections_visibility?.activity && <a href="#activity" className="hover:text-accent transition-colors duration-300">Activity</a>}
          {sections_visibility?.achievements && <a href="#achievements" className="hover:text-accent transition-colors duration-300">Milestones</a>}
          {sections_visibility?.projects && <a href="#projects" className="hover:text-accent transition-colors duration-300">Work</a>}
          {sections_visibility?.testimonials && <a href="#testimonials" className="hover:text-accent transition-colors duration-300">Praise</a>}
          {sections_visibility?.blog && <a href="#blog" className="hover:text-accent transition-colors duration-300">Blog</a>}
          {sections_visibility?.contact && <a href="#contact" className="hover:text-accent transition-colors duration-300">Contact</a>}
          {sections_visibility?.research && <a href="#research" className="hover:text-accent transition-colors duration-300">Research</a>}
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
