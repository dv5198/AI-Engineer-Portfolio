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
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, ease: "easeOut", delay: idx * 0.1 }}
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
            {project.techStack && (
              <span className="font-mono text-[9px] uppercase tracking-widest text-textPrimary/50">
                {project.techStack}
              </span>
            )}
          </div>
          
          <div className="flex gap-6">
            <a href={project.github} target="_blank" rel="noopener noreferrer" className="text-textPrimary/40 hover:text-textPrimary transition-colors">
              <GithubIcon size={16} />
            </a>
            {project.demo && (
              <a href={project.demo} target="_blank" rel="noopener noreferrer" className="text-textPrimary/40 hover:text-textPrimary transition-colors">
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
        const res = await fetch('http://localhost:8000/api/projects/');
        if (!res.ok) throw new Error();
        const githubRepos = await res.json();
        
        // Combine Admin Projects with GitHub Repos
        // Priority: Admin Manual Projects > GitHub Repos
        const adminProjects = data.projects || [];
        const combined = [...adminProjects];
        
        // Add repos that aren't already in manual projects
        githubRepos.forEach(repo => {
          if (!combined.some(p => p.name === repo.name)) {
            combined.push({
              name: repo.name,
              description: repo.description,
              techStack: repo.language,
              github: repo.html_url,
              demo: repo.homepage,
              visible: true
            });
          }
        });

        setProjects(combined);
      } catch (err) {
        setProjects(data.projects || [
          { name: 'antigravity-core', description: 'Deep learning vision model.', github: '#', techStack: 'Python' },
          { name: 'ivory-systems', description: 'React FastAPI dynamic portfolio.', github: '#', techStack: 'JavaScript' }
        ]);
      } finally {
        setLoading(false);
      }
    };
    if (data) fetchProjects();
  }, [data]);

  if (!data || !data.sections_visibility?.projects) return null;

  return (
    <section id="projects" className="pt-16 pb-8 px-6">
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
            {projects.filter(proj => proj.visible !== false && data.project_visibility?.[proj.name] !== false).map((proj, idx) => (
              <ProjectCard key={proj.name} project={proj} idx={idx} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default Projects;
