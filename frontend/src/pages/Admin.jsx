import React, { useContext, useState, useEffect } from 'react';
import { AdminContext } from '../context/AdminContext';
import { PortfolioContext } from '../context/PortfolioContext';

const Admin = () => {
  const { isAuthenticated, login, logout, token } = useContext(AdminContext);
  const { data, fetchPortfolio, updatePortfolio } = useContext(PortfolioContext);
  
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [command, setCommand] = useState('');
  const [cmdResult, setCmdResult] = useState(null);
  
  // Local state for edits
  const [formData, setFormData] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [allProjects, setAllProjects] = useState([]);

  useEffect(() => {
    if (data) {
      setFormData(JSON.parse(JSON.stringify(data))); // deep copy
    }
  }, [data]);

  useEffect(() => {
    if (isAuthenticated) {
      fetch('http://localhost:8000/api/admin/projects/all')
        .then(res => res.json())
        .then(data => setAllProjects(data))
        .catch(err => console.error(err));
    }
  }, [isAuthenticated]);

  const handleLogin = async (e) => {
    e.preventDefault();
    const success = await login(password);
    if (!success) setError('Invalid password');
  };

  const saveChanges = async () => {
    await updatePortfolio(formData);
    alert('Changes saved successfully!');
  };

  const handleChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: { ...prev[section], [field]: value }
    }));
  };

  const handleAboutChange = (idx, value) => {
    const newAbout = [...formData.about];
    newAbout[idx] = value;
    setFormData(prev => ({ ...prev, about: newAbout }));
  };
  
  const handleSkillsChange = (val) => {
    const newSkills = val.split(',').map(s => s.trim()).filter(s => s);
    setFormData(prev => ({ ...prev, skills: newSkills }));
  };

  const handleCommand = async (e) => {
    e.preventDefault();
    setCmdResult('Processing...');
    try {
      const res = await fetch('http://localhost:8000/api/admin/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      });
      const resData = await res.json();
      setCmdResult(JSON.stringify(resData.changes_applied, null, 2));
      await fetchPortfolio(); // refresh to show changes
    } catch (err) {
      setCmdResult('Error executing command');
    }
  };

  const handleAIAction = async (endpoint, payload, callback) => {
    try {
      const res = await fetch(`http://localhost:8000/api/admin/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      callback(data.rewritten);
    } catch (err) {
      alert('AI Action failed');
    }
  };

  const uploadResume = async () => {
    if (!resumeFile) return;
    const body = new FormData();
    body.append("file", resumeFile);
    try {
      await fetch('http://localhost:8000/api/resume', { method: 'POST', body });
      alert('Resume Uploaded');
    } catch (err) {
      alert('Upload failed');
    }
  };

  const deleteResume = async () => {
    try {
      await fetch('http://localhost:8000/api/resume', { method: 'DELETE' });
      alert('Resume Deleted');
    } catch (err) {
      alert('Delete failed');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center relative z-20">
        <form onSubmit={handleLogin} className="bg-white p-8 border border-gray-200 shadow-sm flex flex-col gap-4 max-w-sm w-full">
          <h2 className="text-2xl font-serif text-center mb-4">Admin Access</h2>
          {error && <p className="text-red-500 text-sm text-center font-mono">{error}</p>}
          <input 
            type="password" 
            placeholder="Passphrase" 
            className="border-b border-gray-300 p-2 focus:outline-none focus:border-accent font-mono text-center"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit" className="bg-textPrimary text-white py-3 mt-4 font-mono text-sm tracking-widest uppercase hover:bg-black transition-colors">
            Enter
          </button>
        </form>
      </div>
    );
  }

  if (!formData) return <div>Loading...</div>;

  return (
    <div className="min-h-screen bg-background pt-12 pb-24 px-6 relative z-20">
      <div className="max-w-5xl mx-auto space-y-12">
        
        {/* Header */}
        <div className="flex justify-between items-center border-b border-gray-200 pb-6">
          <h1 className="text-4xl font-serif">Command Center</h1>
          <button onClick={logout} className="text-sm font-mono tracking-widest border border-textPrimary px-4 py-2 hover:bg-textPrimary hover:text-white transition-colors">
            LOGOUT
          </button>
        </div>

        {/* AI Command Line */}
        <div className="bg-white p-6 border border-gray-200 shadow-sm">
          <h3 className="font-mono text-sm mb-4 tracking-widest text-accent font-bold">Terminal_AI</h3>
          <form onSubmit={handleCommand} className="flex gap-4">
            <input 
              type="text" 
              placeholder="e.g. 'Turn off the contact section' or 'Update years experience to 5'" 
              className="flex-1 border bg-gray-50 border-gray-200 p-3 font-mono text-sm focus:outline-none focus:border-accent"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
            />
            <button type="submit" className="bg-textPrimary text-white px-6 font-mono text-sm hover:bg-black">Execute</button>
          </form>
          {cmdResult && (
            <pre className="mt-4 p-4 bg-gray-900 text-green-400 font-mono text-xs overflow-x-auto">
              {cmdResult}
            </pre>
          )}
        </div>

        {/* Editors Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* Profile Editor */}
          <div className="bg-white p-6 border border-gray-200 shadow-sm space-y-4">
            <h3 className="font-serif text-xl border-b pb-2">Profile</h3>
            {['name', 'role', 'email', 'github', 'linkedin'].map(field => (
              <div key={field}>
                <label className="block text-xs font-mono text-gray-500 mb-1 uppercase bg-white">{field}</label>
                <input 
                  className="w-full border-b border-gray-200 py-1 focus:outline-none focus:border-accent font-body"
                  value={formData.profile[field]} 
                  onChange={e => handleChange('profile', field, e.target.value)} 
                />
              </div>
            ))}
            <div>
              <label className="block text-xs font-mono text-gray-500 mb-1 uppercase flex justify-between">
                Bio 
                <button 
                  onClick={() => handleAIAction('rewrite-bio', {text: formData.profile.bio}, (newText) => handleChange('profile', 'bio', newText))}
                  className="text-accent hover:underline"
                >✦ AI Magic</button>
              </label>
              <textarea 
                className="w-full border border-gray-200 p-2 focus:outline-none focus:border-accent font-body h-24"
                value={formData.profile.bio} 
                onChange={e => handleChange('profile', 'bio', e.target.value)} 
              />
            </div>
            <button onClick={saveChanges} className="w-full py-2 bg-textPrimary text-white font-mono text-xs">SAVE PROFILE</button>
          </div>

          {/* About Editor */}
          <div className="bg-white p-6 border border-gray-200 shadow-sm space-y-4">
            <h3 className="font-serif text-xl border-b pb-2 flex justify-between items-center">
              About Text
              <button 
                onClick={() => handleAIAction('rewrite-about', {text: formData.about.join('\n')}, (newText) => setFormData(p => ({...p, about: newText.split('\n')})))}
                className="text-accent font-mono text-xs hover:underline"
              >✦ Enrich All</button>
            </h3>
            {formData.about.map((para, idx) => (
              <textarea 
                key={idx}
                className="w-full border border-gray-200 p-2 focus:outline-none focus:border-accent font-body text-sm h-24"
                value={para} 
                onChange={e => handleAboutChange(idx, e.target.value)} 
              />
            ))}
            <button onClick={saveChanges} className="w-full py-2 bg-textPrimary text-white font-mono text-xs">SAVE ABOUT</button>
          </div>

          {/* Stats & Skills */}
          <div className="bg-white p-6 border border-gray-200 shadow-sm space-y-6">
            <div>
              <h3 className="font-serif text-xl border-b pb-2 mb-4">Stats</h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.keys(formData.stats).map(stat => (
                  <div key={stat}>
                    <label className="block text-xs font-mono text-gray-500 mb-1 uppercase truncate">{stat.replace('_', ' ')}</label>
                    <input 
                      className="w-full border-b border-gray-200 py-1 focus:outline-none focus:border-accent font-mono text-center"
                      value={formData.stats[stat]} 
                      onChange={e => handleChange('stats', stat, e.target.value)} 
                    />
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-serif text-xl border-b pb-2 mb-4">Skills (Comma Separated)</h3>
              <textarea 
                className="w-full border border-gray-200 p-2 focus:outline-none focus:border-accent font-mono text-sm h-24"
                value={formData.skills.join(', ')} 
                onChange={e => handleSkillsChange(e.target.value)} 
              />
            </div>
            <button onClick={saveChanges} className="w-full py-2 bg-textPrimary text-white font-mono text-xs">SAVE STATS & SKILLS</button>
          </div>

          {/* Visibility & Resume */}
          <div className="bg-white p-6 border border-gray-200 shadow-sm space-y-8">
            <div>
              <h3 className="font-serif text-xl border-b pb-2 mb-4">Section Visibility</h3>
              <div className="space-y-3">
                {Object.keys(formData.sections_visibility).map(sec => (
                  <div key={sec} className="flex justify-between items-center border-b border-gray-100 pb-2">
                    <span className="font-mono text-sm capitalize">{sec}</span>
                    <button 
                      onClick={() => {
                        const newVal = !formData.sections_visibility[sec];
                        handleChange('sections_visibility', sec, newVal);
                        updatePortfolio({...formData, sections_visibility: {...formData.sections_visibility, [sec]: newVal}});
                      }}
                      className={`px-3 py-1 text-xs font-mono w-16 ${formData.sections_visibility[sec] ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {formData.sections_visibility[sec] ? 'ON' : 'OFF'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="font-serif text-xl border-b pb-2 mb-4">Project Visibility</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                {allProjects.map(proj => {
                   // By default it is ON if not explicitly set to false
                   const isVisible = formData.project_visibility[proj.name] !== false;
                   return (
                  <div key={proj.name} className="flex justify-between items-center border-b border-gray-100 pb-2">
                    <span className="font-mono text-sm max-w-[150px] truncate" title={proj.name}>{proj.name}</span>
                    <button 
                      onClick={() => {
                        const newVal = !isVisible;
                        handleChange('project_visibility', proj.name, newVal);
                        updatePortfolio({...formData, project_visibility: {...formData.project_visibility, [proj.name]: newVal}});
                      }}
                      className={`px-3 py-1 text-xs font-mono w-16 ${isVisible ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {isVisible ? 'ON' : 'OFF'}
                    </button>
                  </div>
                )})}
                {allProjects.length === 0 && <p className="text-xs font-mono text-gray-500">No projects found. Check GitHub handle.</p>}
              </div>
            </div>
            
            <div className="border border-gray-100 p-6 bg-white space-y-6">
              <div className="flex justify-between items-center border-b pb-2">
                <h3 className="font-serif text-xl">Experience</h3>
                <button 
                  onClick={() => {
                    const newVal = !formData.sections_visibility?.experience;
                    setFormData({...formData, sections_visibility: {...formData.sections_visibility, experience: newVal}});
                  }}
                  className={`px-3 py-1 text-[10px] font-mono rounded ${formData.sections_visibility?.experience ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                >
                  SECTION {formData.sections_visibility?.experience ? 'VISIBLE' : 'HIDDEN'}
                </button>
              </div>
              <div className="space-y-4">
                {formData.experience?.map((job, idx) => (
                  <div key={idx} className="p-4 border border-gray-100 space-y-2">
                    <input 
                      placeholder="Company" 
                      className="w-full border-b text-xs font-mono p-1"
                      value={job.company} 
                      onChange={e => {
                        const newExp = [...formData.experience];
                        newExp[idx].company = e.target.value;
                        setFormData({...formData, experience: newExp});
                      }}
                    />
                    <input 
                      placeholder="Position" 
                      className="w-full border-b text-xs font-mono p-1"
                      value={job.position} 
                      onChange={e => {
                        const newExp = [...formData.experience];
                        newExp[idx].position = e.target.value;
                        setFormData({...formData, experience: newExp});
                      }}
                    />
                    <div className="flex gap-2">
                      <input 
                        placeholder="Start" 
                        className="flex-1 border-b text-xs font-mono p-1"
                        value={job.start} 
                        onChange={e => {
                          const newExp = [...formData.experience];
                          newExp[idx].start = e.target.value;
                          setFormData({...formData, experience: newExp});
                        }}
                      />
                      <input 
                        placeholder="End (e.g. Present)" 
                        className="flex-1 border-b text-xs font-mono p-1"
                        value={job.end} 
                        onChange={e => {
                          const newExp = [...formData.experience];
                          newExp[idx].end = e.target.value;
                          setFormData({...formData, experience: newExp});
                        }}
                      />
                      <button 
                        onClick={() => {
                          const newExp = formData.experience.filter((_, i) => i !== idx);
                          setFormData({...formData, experience: newExp});
                        }}
                        className="px-2 text-red-500 hover:bg-red-50 transition-colors"
                        title="Delete Experience"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                      </button>
                    </div>
                  </div>
                ))}
                <button 
                  onClick={() => setFormData({...formData, experience: [...(formData.experience || []), {company:'', position:'', start:'', end:'', description:''}]})}
                  className="w-full py-2 border border-dashed border-gray-300 text-gray-400 font-mono text-[10px] hover:border-accent hover:text-accent"
                >+ ADD JOB</button>
              </div>
            </div>

            <div className="border border-gray-100 p-6 bg-white space-y-6">
              <div className="flex justify-between items-center border-b pb-2">
                <h3 className="font-serif text-xl">Achievements</h3>
                <button 
                  onClick={() => {
                    const newVal = !formData.sections_visibility?.achievements;
                    setFormData({...formData, sections_visibility: {...formData.sections_visibility, achievements: newVal}});
                  }}
                  className={`px-3 py-1 text-[10px] font-mono rounded ${formData.sections_visibility?.achievements ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                >
                  SECTION {formData.sections_visibility?.achievements ? 'VISIBLE' : 'HIDDEN'}
                </button>
              </div>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 border border-gray-200">
                  <label className="block text-[10px] font-mono text-gray-400 uppercase mb-2">Achievement Photo (optional)</label>
                  {formData.achievement_image?.url ? (
                    <div className="relative group">
                      <img src={formData.achievement_image.url} className="w-full h-32 object-cover border border-gray-200" />
                      <button 
                         onClick={() => setFormData({...formData, achievement_image: {url: '', caption: ''}})}
                         className="absolute top-2 right-2 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                      </button>
                    </div>
                  ) : (
                    <input 
                      type="file" 
                      accept="image/*"
                      onChange={async (e) => {
                        const file = e.target.files[0];
                        if (!file) return;
                        const body = new FormData();
                        body.append('file', file);
                        const res = await fetch('http://localhost:8000/api/admin/achievement-image', { method: 'POST', body });
                        const resData = await res.json();
                        setFormData({...formData, achievement_image: { ...formData.achievement_image, url: resData.url }});
                      }}
                      className="font-mono text-[10px]"
                    />
                  )}
                  <input 
                    placeholder="Photo Caption" 
                    className="w-full border-b bg-transparent text-[10px] font-mono mt-2 p-1"
                    value={formData.achievement_image?.caption || ''} 
                    onChange={e => setFormData({...formData, achievement_image: {...formData.achievement_image, caption: e.target.value}})}
                  />
                </div>
                {formData.achievements?.map((ach, idx) => (
                  <div key={idx} className="p-4 border border-gray-100 space-y-2 relative group-item">
                    <div className="flex justify-between items-center bg-white">
                      <input 
                        placeholder="Achievement Title" 
                        className="flex-1 border-b text-xs font-mono p-1"
                        value={ach.title} 
                        onChange={e => {
                          const newAch = [...formData.achievements];
                          newAch[idx].title = e.target.value;
                          setFormData({...formData, achievements: newAch});
                        }}
                      />
                      <button 
                        onClick={() => {
                          const newAch = formData.achievements.filter((_, i) => i !== idx);
                          setFormData({...formData, achievements: newAch});
                        }}
                        className="ml-2 text-red-500 hover:bg-red-50 p-1"
                        title="Delete Achievement"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                      </button>
                    </div>
                    <textarea 
                      placeholder="Description" 
                      className="w-full border p-2 text-xs font-mono h-16"
                      value={ach.description} 
                      onChange={e => {
                        const newAch = [...formData.achievements];
                        newAch[idx].description = e.target.value;
                        setFormData({...formData, achievements: newAch});
                      }}
                    />
                  </div>
                ))}
                <button 
                  onClick={() => setFormData({...formData, achievements: [...(formData.achievements || []), {title:'', description:''}]})}
                  className="w-full py-2 border border-dashed border-gray-300 text-gray-400 font-mono text-[10px] hover:border-accent hover:text-accent"
                >+ ADD ACHIEVEMENT</button>
              </div>
            </div>
            
            <button onClick={saveChanges} className="w-full py-3 bg-accent text-white font-mono text-xs tracking-widest uppercase">SAVE CHANGES</button>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Admin;
