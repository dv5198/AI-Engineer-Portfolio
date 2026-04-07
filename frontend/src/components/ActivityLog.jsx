import React, { useEffect, useState } from 'react';
import { ScrollText, Globe, Download, Mail, Activity } from 'lucide-react';

const ActivityLog = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/platform/activity/')
      .then(res => res.json())
      .then(data => {
        setLogs(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const getIcon = (event) => {
    switch (event) {
      case 'page_view': return <Globe size={14} className="text-warmBrown/40" />;
      case 'resume_download': return <Download size={14} className="text-accent" />;
      case 'form_submission': return <Mail size={14} className="text-warmBrown" />;
      default: return <Activity size={14} className="text-warmBrown/20" />;
    }
  };

  if (loading) return <div className="h-64 flex items-center justify-center font-mono text-[10px] text-warmBrown/40">Retrieving system ledger...</div>;

  return (
    <div className="bg-white border border-warmBrown/5 p-8 shadow-sm">
      <div className="flex items-center gap-3 mb-8">
          <ScrollText size={18} className="text-accent" />
          <h3 className="font-serif text-xl">System Ledger</h3>
      </div>

      <div className="space-y-0 border-t border-warmBrown/5">
        {logs.map((log, i) => (
          <div key={i} className="flex items-center gap-6 py-4 border-b border-warmBrown/5 hover:bg-ivory/20 transition-colors px-2">
            <div className="w-8 flex justify-center">
              {getIcon(log.event)}
            </div>
            
            <div className="flex-1">
              <div className="flex justify-between items-start">
                <p className="font-mono text-[10px] uppercase tracking-wider text-warmBrown">
                  {log.event.replace('_', ' ')}
                </p>
                <span className="font-mono text-[9px] text-warmBrown/30">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="font-mono text-[9px] text-warmBrown/40 truncate max-w-md mt-1 italic">
                {log.ip} // {log.userAgent}
              </p>
            </div>
          </div>
        ))}

        {logs.length === 0 && (
          <div className="py-20 text-center font-mono text-[10px] text-warmBrown/30">
            No events recorded in this epoch.
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityLog;
