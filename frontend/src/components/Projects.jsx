import React, { useContext, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';
import { GithubIcon, ExternalLinkIcon } from 'lucide-react';
import { generateProjectCover } from '../utils/imageGenerator';

const ProjectCard = ({ project, idx }) => {
  const [cover, setCover] = useState(null);

  useEffect(() => {
    setCover(generateProjectCover(project.name));
  }, [project.name]);

  return (
    <motion.div
      className="group relative flex flex-col bg-background border border-textPrimary/5 overflow-hidden shadow-none hover:shadow-2xl transition-all duration-700 h-full"
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      animate={{ y: [0, -12, 0] }}
      transition={{
        y: {
          duration: 5 + (idx % 3) * 1.5,
          repeat: Infinity,
          ease: "easeInOut",
          delay: idx * 0.2
        },
        opacity: { duration: 0.8 },
        layout: { duration: 0.3 }
      }}
    >
      <div className="h-56 overflow-hidden relative border-b border-textPrimary/5">
        {cover ? (
          <img 
            src={cover} 
            alt={project.name} 
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-1000 grayscale-[0.2] group-hover:grayscale-0"
          />
        ) : (
          <div className="w-full h-full bg-[#f2ede0] animate-pulse" />
        )}
      </div>
      
      <div className="p-8 flex-grow flex flex-col">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-3xl font-serif text-textPrimary leading-tight">
            {project.name}
          </h3>
          <span className="font-mono text-[10px] text-textPrimary/40 uppercase tracking-widest pt-2">
            OBJ_{idx.toString().padStart(2, '0')}
          </span>
        </div>
        
        <p className="text-lg font-serif italic text-textPrimary/70 leading-relaxed mb-8 line-clamp-3">
          {project.summary || project.description || `A technical investigation into ${project.language || 'modern systems'}.`}
        </p>

        <div className="mt-auto pt-6 flex items-center justify-between border-t border-textPrimary/5">
          <div className="flex gap-4">
            {project.language && (
              <span className="font-mono text-[9px] uppercase tracking-widest text-textPrimary/50">
                {project.language}
              </span>
            )}
          </div>
          
          <div className="flex gap-6">
            <a href={project.html_url} target="_blank" rel="noopener noreferrer" className="text-textPrimary/40 hover:text-textPrimary transition-colors">
              <GithubIcon size={16} />
            </a>
            {project.homepage && (
              <a href={project.homepage} target="_blank" rel="noopener noreferrer" className="text-textPrimary/40 hover:text-textPrimary transition-colors">
                <ExternalLinkIcon size={16} />
              </a>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const Projects = () => {
  const { data } = useContext(PortfolioContext);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/projects');
        if (!res.ok) throw new Error();
        const json = await res.json();
        setProjects(json);
      } catch (err) {
        setProjects([
          { name: 'antigravity-core', description: 'Deep learning vision model.', html_url: '#', language: 'Python' },
          { name: 'ivory-systems', description: 'React FastAPI dynamic portfolio.', html_url: '#', language: 'JavaScript' },
          { name: 'monolith-db', description: 'Blazing fast system metrics tool.', html_url: '#', language: 'Rust' }
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  if (!data || !data.sections_visibility?.projects) return null;

  return (
    <section id="projects" className="py-32 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-24 flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="max-w-2xl">
            <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-6">Archive // 2024</p>
            <h2 className="text-6xl md:text-8xl font-serif text-textPrimary italic">Featured Work</h2>
          </div>
          <p className="font-mono text-[10px] text-textPrimary/40 uppercase tracking-widest text-right">
            Deterministic Generation<br/>Ready for Inspection
          </p>
        </div>

        {loading ? (
          <div className="h-96 flex items-center justify-center font-mono text-xs uppercase tracking-widest opacity-30">
            Fetching Systems...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
            {projects.map((proj, idx) => (
              <ProjectCard key={proj.name} project={proj} idx={idx} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default Projects;
