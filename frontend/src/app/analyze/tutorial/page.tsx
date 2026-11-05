'use client';
import { GridBackground } from '@/components/GridBackground';
import React, { useEffect, useState } from 'react';
import Loading from '@/components/Loading';
import FileTutorial from '@/components/Tutorial/FileTutorial';
import { FileCodeViewer } from '@/components/FileAnalysis/FileCodeViewer';
import { motion } from 'framer-motion';
import { FileAnalysis, TutorialStep } from '@/types/file_analysis_type';
import FileSelector from '@/components/FileAnalysis/FileSelector';
import { getItem } from '@/utils/indexedDB';

function Tutorial() {
  const [fileAnalysis, setFileAnalysis] = useState<FileAnalysis | null>(null);
  const [currentFile, setCurrentFile] = useState<string>('Choose a file to view its tutorial.');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('Retrieving file contents...');
  const [showCodeViewer, setShowCodeViewer] = useState(false);

  useEffect(() => {
    async function fetchTutorial(){
    const file = await getItem<string>('lastUsedFile');
    if (!file) {
      setMessage('No file selected. Please select a file from architecture map.');
      setLoading(false);
      return;
    }
    setCurrentFile(file);
    const storageKey = `fileAnalysis-${file}`;
    const file_analysis = await getItem<FileAnalysis>(storageKey);

    if (file_analysis) {
      setFileAnalysis(file_analysis);
    }
    setLoading(false);
  }
  fetchTutorial()
  }, []);

  const extractHighlightedLines = (): number[] => {
    const steps = fileAnalysis?.analysis?.tutorial ?? [];
    const allLines = new Set<number>();

    steps.forEach((step: TutorialStep) => {
      if (Array.isArray(step.lines)) {
        step.lines.forEach((line: number | [number, number]) => {
          if (Array.isArray(line)) {
            const [start, end] = line;
            for (let i = start; i <= end; i++) {
              allLines.add(i);
            }
          } else {
            allLines.add(line);
          }
        });
      }
    });

    return Array.from(allLines).sort((a, b) => a - b);
  };

  if (loading) return <Loading message={message} />;

  const highlightLines = extractHighlightedLines();

  return (
    <div className="h-screen flex flex-col items-center w-full relative overflow-y-auto scroll-smooth">
      <div className="fixed h-screen w-full">
          <GridBackground />
        </div>

      <motion.div
      initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
       className='w-full p-10 flex items-center'>
        {/* Heading */}
        <h1 className="relative text-xl pr-4  text-left lg:text-3xl z-20 font-bold bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400 bg-opacity-50">
          <span className="relative bg-clip-text text-transparent bg-no-repeat bg-gradient-to-r from-purple-500 via-violet-500 to-pink-500 py-4">
            Tutorial:
          </span> 
        </h1>
        <FileSelector  selectedFile={currentFile} onFileSelect={()=>{window.location.reload()}}/>
      </motion.div>

    {Array.isArray(fileAnalysis?.analysis?.tutorial) &&
            fileAnalysis.analysis.tutorial.length > 0 ? (
        <>
      {/* Mobile Toggle Button */}
      {!showCodeViewer && (
        <button
          className="fixed top-20 right-6 z-30 bg-purple-600 text-white px-4 py-2 rounded-full shadow-md lg:hidden"
          onClick={() => setShowCodeViewer(true)}
        >
          View Code
        </button>
      )}


      {/* Main Tutorial Content */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative z-10 flex justify-center items-center gap-4 w-[80%] h-[70vh]"
      >
        
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut', delay: 0.1 }}
            className="z-10 w-full h-full flex justify-center items-center"
          >
            <FileTutorial steps={fileAnalysis.analysis.tutorial} />
          </motion.div>


        {/* Code viewer for desktop */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
          className="max-w-xl h-full  justify-center items-center w-full hidden lg:flex"
        >
          {fileAnalysis && (
            <FileCodeViewer
            filename={currentFile}
            language={fileAnalysis?.analysis.language}
            code={fileAnalysis?.analysis.code}
            highlightLines={highlightLines}
            />)
          }
        </motion.div>
      </motion.div>

      {/* Slide-in Code Viewer for Mobile */}
      <motion.div
        className="fixed top-0 right-0 h-full w-full sm:w-[90vw] bg-[#121212] z-40 p-4 lg:hidden"
        initial={{ x: '100%' }}
        animate={{ x: showCodeViewer ? 0 : '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        <div className="flex justify-end mb-2">
          <button
            onClick={() => setShowCodeViewer(false)}
            className="text-white bg-neutral-700 px-3 py-1 rounded-md"
          >
            Close
          </button>
        </div>
        {fileAnalysis && (
            <FileCodeViewer
            filename={currentFile}
            language={fileAnalysis?.analysis.language}
            code={fileAnalysis?.analysis.code}
            highlightLines={highlightLines}
            />)
          }
      </motion.div>
      </>
              ) : (
          <div className="relative -mt-32 z-20 w-full h-screen flex justify-center items-center px-6">
            <div className="max-w-2xl text-center">
              <h2 className="text-2xl font-bold bg-gradient-to-b from-neutral-200 to-neutral-500 bg-clip-text text-transparent mb-4">
                {fileAnalysis?.analysis?.auth_required 
                  ? "AI Features Locked" 
                  : "Tutorial Not Available"}
              </h2>
              <p className="text-neutral-400 text-lg mb-6">
                {fileAnalysis?.analysis?.summary || 
                 "AI-powered tutorials are only available to logged-in users. Sign up or log in to unlock AI features including detailed file summaries and step-by-step tutorials!"}
              </p>
              {fileAnalysis?.analysis?.auth_required && (
                <div className="flex gap-4 justify-center">
                  <a 
                    href="/login" 
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors"
                  >
                    Log In
                  </a>
                  <a 
                    href="/signup" 
                    className="px-6 py-3 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg font-semibold transition-colors"
                  >
                    Sign Up
                  </a>
                </div>
              )}
            </div>
          </div>
        )}
    </div>
  );
}

export default Tutorial;
