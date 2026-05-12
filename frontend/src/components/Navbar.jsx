import React, { useContext, useEffect, useState } from 'react';
import { PortfolioContext } from '../context/PortfolioContext';
import { Moon, Sun } from 'lucide-react';

import { Menu, X } from 'lucide-react';

const Navbar = () => {
  const { data } = useContext(PortfolioContext);
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
        <a href="#hero" className="font-serif text-xl md:text-2xl font-bold tracking-tight transition-colors">
          {profile?.name}
        </a>

        {/* Links */}
        <div className="hidden md:flex gap-6 items-center font-mono text-[9px] uppercase tracking-[0.2em]">
          {sections_visibility?.about && <a href="#about" className="hover:text-accent transition-colors duration-300">About</a>}
          {sections_visibility?.experience && <a href="#experience" className="hover:text-accent transition-colors duration-300">Experience</a>}
          {sections_visibility?.skills && <a href="#skills" className="hover:text-accent transition-colors duration-300">Skills</a>}
          {sections_visibility?.projects && <a href="#projects" className="hover:text-accent transition-colors duration-300">Work</a>}
          {sections_visibility?.blog && <a href="#blog" className="hover:text-accent transition-colors duration-300">Blog</a>}
          {sections_visibility?.research && <a href="#research" className="hover:text-accent transition-colors duration-300">Research</a>}
        </div>

        {/* Mobile Menu Button */}
        <div className="md:hidden flex items-center">
          <button 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 -mr-2 text-warmBlack hover:text-accent transition-colors"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

      </div>

      {/* Mobile Dropdown Menu */}
      <div 
        className={`md:hidden absolute top-full left-0 w-full bg-ivory shadow-lg border-b border-warmBlack/5 transition-all duration-300 overflow-hidden ${
          mobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="flex flex-col px-6 py-4 gap-4 font-mono text-xs uppercase tracking-[0.2em]">
          {sections_visibility?.about && <a href="#about" onClick={() => setMobileMenuOpen(false)} className="hover:text-accent py-2 transition-colors">About</a>}
          {sections_visibility?.experience && <a href="#experience" onClick={() => setMobileMenuOpen(false)} className="hover:text-accent py-2 transition-colors">Experience</a>}
          {sections_visibility?.skills && <a href="#skills" onClick={() => setMobileMenuOpen(false)} className="hover:text-accent py-2 transition-colors">Skills</a>}
          {sections_visibility?.projects && <a href="#projects" onClick={() => setMobileMenuOpen(false)} className="hover:text-accent py-2 transition-colors">Work</a>}
          {sections_visibility?.blog && <a href="#blog" onClick={() => setMobileMenuOpen(false)} className="hover:text-accent py-2 transition-colors">Blog</a>}
          {sections_visibility?.research && <a href="#research" onClick={() => setMobileMenuOpen(false)} className="hover:text-accent py-2 transition-colors">Research</a>}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
