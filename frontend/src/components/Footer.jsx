import React from 'react';

const Footer = () => {
  return (
    <footer className="py-12 px-6 bg-contactBg text-background relative z-10 border-t border-background/5">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        <p className="font-mono text-[9px] uppercase tracking-widest text-background/40 order-2 md:order-1">
          &copy; {new Date().getFullYear()} Divya Nirankari. All Rights Reserved.
        </p>
        <p className="font-serif italic text-lg text-background/60 order-1 md:order-2">
          Software Engineer & AI Research Advocate
        </p>
      </div>
    </footer>
  );
};

export default Footer;
