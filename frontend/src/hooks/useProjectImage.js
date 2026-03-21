import { useState, useEffect } from 'react';

export const useProjectImage = (repoName, topics = []) => {
  const [dataUrl, setDataUrl] = useState(null);

  useEffect(() => {
    if (!repoName) return;

    const getSearchTerms = (name, tpc) => {
      const lowerName = name.toLowerCase();
      
      // Keywords mapping based on common project types
      if (lowerName.includes('ecommerce') || lowerName.includes('shop') || lowerName.includes('store')) return "shopping,store,ecommerce,app";
      if (lowerName.includes('portfolio') || lowerName.includes('resume')) return "website,design,modern,portfolio";
      if (lowerName.includes('ml') || lowerName.includes('ai') || lowerName.includes('model') || lowerName.includes('deep')) return "artificial-intelligence,data,code,technology";
      if (lowerName.includes('app') || lowerName.includes('mobile')) return "smartphone,mobile-app,ui";
      if (lowerName.includes('game')) return "videogame,gaming,play";
      if (lowerName.includes('admin') || lowerName.includes('dashboard')) return "dashboard,analytics,chart";
      
      // Fallback: use topics if available, else clean repo name
      return tpc && tpc.length > 0 ? tpc[0] : name.replace(/-/g, ',');
    };

    const searchTerms = getSearchTerms(repoName, topics);

    // Unsplash Source API provides a clean way to fetch random contextual images
    // Note: To avoid browser caching loading the exact same image for every project,
    // we append the repoName as a unique signature query parameter.
    const imageUrl = `https://source.unsplash.com/600x400/?${encodeURIComponent(searchTerms)}&sig=${encodeURIComponent(repoName)}`;
    
    setDataUrl(imageUrl);
  }, [repoName, topics]);

  return dataUrl;
};
