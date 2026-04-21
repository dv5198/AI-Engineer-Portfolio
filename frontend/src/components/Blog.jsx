import React, { useContext, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';
import ReactMarkdown from 'react-markdown';
import { X } from 'lucide-react';

const Blog = () => {
  const { data } = useContext(PortfolioContext);
  const [selectedPost, setSelectedPost] = useState(null);

  if (!data || !data.sections_visibility?.blog) return null;

  const posts = data.blogPosts?.filter(p => p.visible !== false) || [];

  const calculateReadingTime = (content) => {
    const wordsPerMinute = 200;
    const words = content.trim().split(/\s+/).length;
    return Math.ceil(words / wordsPerMinute);
  };

  return (
    <section id="blog" className="py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20 flex justify-between items-end">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-warmBrown/40 mb-4 italic text-right md:text-left">Archives // 06</p>
            <h2 className="text-5xl md:text-6xl font-serif text-warmBrown italic">Thought Canvas</h2>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
          {posts.map((post, idx) => (
            <motion.div
              key={post.id || idx}
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 6, repeat: Infinity, delay: idx * 0.2, ease: "easeInOut" }}
              onClick={() => {
                if (post.url) {
                  window.open(post.url, '_blank');
                } else {
                  setSelectedPost(post);
                }
              }}
              className="group cursor-pointer"
            >
              <div className="bg-ivory-deep/20 border border-warmBrown/5 p-8 h-full hover:border-accent/40 transition-all duration-500 hover:shadow-2xl">
                <span className="font-mono text-[9px] text-accent uppercase tracking-widest mb-4 block">
                  {post.category} — {calculateReadingTime(post.content)} min read
                </span>
                <h3 className="text-2xl font-serif text-warmBrown group-hover:text-accent transition-colors duration-300 mb-4 leading-tight">
                  {post.title}
                </h3>
                <p className="text-sm font-sans text-warmBrown/60 line-clamp-3 mb-6">
                  {post.content.substring(0, 150)}...
                </p>
                <div className="flex justify-between items-center pt-6 border-t border-warmBrown/5">
                    <span className="font-mono text-[10px] text-warmMid">{new Date(post.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                    <span className="font-mono text-[10px] text-accent hover:underline flex items-center gap-1">
                      {post.url ? 'Visit Link →' : 'Read →'}
                    </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Modal Reader */}
      <AnimatePresence>
        {selectedPost && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-12">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedPost(null)}
              className="absolute inset-0 bg-warmBlack/80 backdrop-blur-sm"
            />
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              className="bg-ivory w-full max-w-4xl max-h-full overflow-y-auto relative z-10 p-8 md:p-16 shadow-2xl"
            >
              <button 
                onClick={() => setSelectedPost(null)}
                className="absolute top-8 right-8 text-warmBrown/40 hover:text-accent transition-colors"
              >
                <X size={24} />
              </button>

              <div className="max-w-2xl mx-auto">
                <span className="font-mono text-[10px] text-accent uppercase tracking-widest mb-4 block">
                  {selectedPost.category} // {new Date(selectedPost.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
                </span>
                <h1 className="text-4xl md:text-5xl font-serif text-warmBrown mb-12 italic leading-tight">
                  {selectedPost.title}
                </h1>
                
                <div className="prose prose-stone max-w-none font-sans text-warmBrown/80 leading-relaxed space-y-6">
                  <ReactMarkdown>{selectedPost.content}</ReactMarkdown>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  );
};

export default Blog;
