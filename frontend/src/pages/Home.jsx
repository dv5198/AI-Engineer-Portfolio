import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import About from '../components/About';
import Skills from '../components/Skills';
import Projects from '../components/Projects';
import Experience from '../components/Experience';
import Achievements from '../components/Achievements';
import Contact from '../components/Contact';
import Footer from '../components/Footer';
import ActivityHeatmap from '../components/ActivityHeatmap';
import Research from '../components/Research';
import Testimonials from '../components/Testimonials';
import Blog from '../components/Blog';
import Loader from '../components/Loader';

const Home = () => {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const shown = sessionStorage.getItem('intro_shown');
    if (!shown) {
      setLoading(true);
      sessionStorage.setItem('intro_shown', 'true');
    }

    // Log Analytics Event
    fetch('http://localhost:8001/api/platform/event/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event: 'page_view', data: { path: '/' } })
    }).catch(err => console.error('Analytics log failed', err));
  }, []);

  return (
    <>
      {loading && <Loader onComplete={() => setLoading(false)} />}
      <div className={`relative ${loading ? 'opacity-0' : 'opacity-100 transition-opacity duration-1000'}`}>
        <Navbar />
        <main className="w-full">
          <Hero />
          <About />
          <Experience />
          <Skills />
          <ActivityHeatmap />
          <Achievements />
          <Projects />
          <Testimonials />
          <Blog />
          <Contact />
          <Research />
        </main>
        <Footer />
      </div>
    </>
  );
};

export default Home;
