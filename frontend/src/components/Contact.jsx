import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';
import { Mail, Github, Linkedin } from 'lucide-react';

const Contact = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.contact) return null;

  const { profile } = data;

  const links = [
    {
      name: 'GitHub',
      icon: <Github size={20} />,
      url: profile.github
    },
    {
      name: 'LinkedIn',
      icon: <Linkedin size={20} />,
      url: profile.linkedin
    },
    {
      name: 'Email',
      icon: <Mail size={20} />,
      url: `mailto:${profile.email}`
    }
  ];

  return (
    <section id="contact" className="py-40 bg-contactBg text-background flex flex-col items-center justify-center relative z-10 px-6">
      <div className="text-center max-w-2xl mb-24">
        {/* <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-background/40 mb-10">I have got just what you need. Lets talk.</p> */}
        <h2 className="text-6xl md:text-8xl font-serif mb-6 italic">Get In Touch</h2>
        <p className="font-serif italic text-2xl text-background/60">
          Interested in the intersection of scalable systems and machine intelligence.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-8 md:gap-16 items-center">
        {links.map((link, idx) => (
          <motion.a
            key={idx}
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-6 px-10 py-5 border border-background/20 rounded-full text-background hover:bg-background hover:text-contactBg transition-all duration-700 shadow-none hover:shadow-2xl"
            animate={{ y: [0, -12, 0] }}
            transition={{
              duration: 5 + (idx * 1.5),
              repeat: Infinity,
              delay: idx * 0.3,
              ease: "easeInOut"
            }}
          >
            {link.icon}
            <span className="font-mono text-xs uppercase tracking-[0.3em] font-medium">{link.name}</span>
          </motion.a>
        ))}
      </div>
    </section>
  );
};

export default Contact;
