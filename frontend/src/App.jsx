import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home.jsx';
import Admin from './pages/Admin.jsx';
import CanvasParticles from './components/CanvasParticles.jsx';
import CustomCursor from './components/CustomCursor.jsx';

function App() {
  return (
    <>
      <CustomCursor />
      <CanvasParticles />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </>
  );
}

export default App;
