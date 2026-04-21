import React, { useEffect, useState, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const ActivityHeatmap = () => {
  const { data: portfolioData } = useContext(PortfolioContext);
  const [contributions, setContributions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hoveredDay, setHoveredDay] = useState(null);

  useEffect(() => {
    if (portfolioData?.profile?.github) {
      const username = portfolioData.profile.github.split('/').pop();
      fetch(`http://localhost:8000/api/platform/github/contributions/?username=${username}`)
        .then(res => res.json())
        .then(data => {
          setContributions(data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [portfolioData]);

  if (!portfolioData?.sections_visibility?.activity) return null;

  const colors = {
    0: "#e8e0d0", 
    1: "#d4c9b0",
    2: "#b5a890",
    3: "#9a7a55",
    4: "#5a4a35"
  };

  const getColor = (count) => {
    if (count === 0) return colors[0];
    if (count <= 3) return colors[1];
    if (count <= 6) return colors[2];
    if (count <= 9) return colors[3];
    return colors[4];
  };

  const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  return (
    <section id="activity" className="py-16 px-6 bg-ivory">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-warmBrown mb-4 text-center">Open Source Activity // 02</p>
          <h2 className="text-5xl md:text-6xl font-serif text-textPrimary text-center italic">Code Pulse</h2>
        </div>

        <div 
          className="bg-ivory p-4 md:p-8 overflow-hidden relative w-full flex justify-center"
        >
          {loading ? (
            <div className="h-40 flex items-center justify-center font-mono text-sm text-warmBrown">
              Synchronizing with GitHub...
            </div>
          ) : contributions?.weeks ? (
            <div className="w-full max-w-[800px]">
              <div className="flex justify-between items-center mb-8">
                <p className="font-mono text-xs text-textPrimary">
                  <span className="text-accent font-bold text-lg mr-2">{contributions.totalContributions}</span> 
                  contributions in the last year
                </p>
                <div className="flex items-center gap-2 text-[10px] font-mono text-warmBrown">
                  <span>Less</span>
                  {[0, 1, 4, 7, 10].map(v => (
                    <div key={v} className="w-3 h-3 rounded-[2px]" style={{ backgroundColor: getColor(v) }} />
                  ))}
                  <span>More</span>
                </div>
              </div>

              <div className="flex">
                <div className="flex flex-col gap-[7px] pr-4 pt-6 text-[9px] font-mono text-warmBrown">
                  <span>Mon</span>
                  <span>Wed</span>
                  <span>Fri</span>
                </div>
                
                <div className="flex-1">
                  <div className="flex mb-2 text-[9px] font-mono text-warmBrown">
                    {monthLabels.map((m, i) => (
                      <span key={i} style={{ width: `${100/12}%` }}>{m}</span>
                    ))}
                  </div>
                  
                  <div className="flex gap-[3px]">
                    {contributions.weeks.map((week, wIdx) => (
                      <div key={wIdx} className="flex flex-col gap-[3px]">
                        {week.contributionDays.map((day, dIdx) => (
                          <div
                            key={dIdx}
                            className="w-[11px] h-[11px] rounded-[2px] cursor-crosshair transition-all duration-300 hover:scale-125"
                            style={{ backgroundColor: getColor(day.contributionCount) }}
                            onMouseEnter={(e) => setHoveredDay({ ...day, x: e.clientX, y: e.clientY })}
                            onMouseLeave={() => setHoveredDay(null)}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
             <div className="h-40 flex items-center justify-center font-mono text-sm text-red-500">
              Unable to fetch contribution data.
            </div>
          )}

          <AnimatePresence>
            {hoveredDay && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                style={{ left: hoveredDay.x - 40, top: hoveredDay.y - 60 }}
                className="fixed z-50 pointer-events-none bg-warmBlack text-ivory text-[10px] font-mono py-2 px-3 rounded shadow-xl whitespace-nowrap"
              >
                {hoveredDay.contributionCount} contributions on {new Date(hoveredDay.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
};

export default ActivityHeatmap;
