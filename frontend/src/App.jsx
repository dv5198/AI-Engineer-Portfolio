import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Home from './pages/Home.jsx';
import Admin from './pages/Admin.jsx';
import CanvasParticles from './components/CanvasParticles.jsx';
import CustomCursor from './components/CustomCursor.jsx';
import Loader from './components/Loader.jsx';

function App() {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const hasShownLoader = sessionStorage.getItem('intro_shown');
    if (!hasShownLoader) {
      setLoading(true);
      sessionStorage.setItem('intro_shown', 'true');
    }
  }, []);

  return (
    <>
      <AnimatePresence>
        {loading && <Loader onComplete={() => setLoading(false)} />}
      </AnimatePresence>
      
      {!loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <CustomCursor />
          <CanvasParticles />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </motion.div>
      )}
    </>
  );
}

export default App;
