import React, { createContext, useState, useEffect } from 'react';

export const PortfolioContext = createContext();

export const PortfolioProvider = ({ children }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Dark mode state removed to stay in Antigravity light theme
  const isDarkMode = false;
  const toggleDarkMode = () => { };

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      // In production, configure API base URL properly (.env)
      const res = await fetch('http://localhost:8001/api/portfolio/');
      if (!res.ok) throw new Error('Failed to fetch portfolio data');
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err.message);
      // Optional: Add Fallback Data here if backend is completely down
      setData({
        profile: {
          name: "Divya Nirankari",
          role: "Software Engineer & AI/ML Engineer",
          bio: "I build scalable web applications and intelligent machine learning models.",
          github: "https://github.com/dv5198",
          linkedin: "https://linkedin.com/in/divya-nirankari",
          email: "dvnirankari@gmail.com"
        },
        about: ["Fallback about section"],
        stats: { projects_count: "10+", years_experience: "3", ml_models: "5", fun_stat: "Lots of code" },
        skills: ["React", "Python", "FastAPI"],
        sections_visibility: { about: true, skills: true, projects: true, contact: true },
        project_visibility: {}
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const updatePortfolio = async (newData) => {
    try {
      const res = await fetch('http://localhost:8001/api/portfolio/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newData)
      });
      if (res.ok) {
        setData(newData);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Update failed', err);
      return false;
    }
  };

  return (
    <PortfolioContext.Provider value={{ data, loading, error, setData, updatePortfolio, fetchPortfolio, isDarkMode, toggleDarkMode }}>
      {children}
    </PortfolioContext.Provider>
  );
};
