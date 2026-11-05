'use client';
import { GridBackground } from '@/components/GridBackground';
import React, { useEffect, useState } from 'react';
import CallGraph from '@/components/Graph/CallGraph';
import Loading from '@/components/Loading';
import { motion } from 'framer-motion';
import { FileAnalysis } from '@/types/file_analysis_type';
import FileSelector from '@/components/FileAnalysis/FileSelector';
import { getItem } from '@/utils/indexedDB';

function ControlFlow() {
  const [fileAnalysis, setFileAnalysis] = useState<FileAnalysis | null>(null);
  const [currentFile, setCurrentFile] = useState<string>('Choose a file to view its call graph.');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('Retrieving file contents...');

  useEffect(() => {
    async function fetchCallGraph(){
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
  fetchCallGraph();
  }, []);

  if (loading) return <Loading message={message} />;

  return (
    <div className="h-screen w-full relative">
      <div className='h-screen fixed w-full'>
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
            Call Graph:
          </span> 
        </h1>
        <FileSelector  selectedFile={currentFile} onFileSelect={()=>{window.location.reload()}}/>
      </motion.div>

      <div className="relative z-10 h-full w-full">
        {fileAnalysis && fileAnalysis?.call_graph?.nodes?.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="h-full w-full"
          >
            <CallGraph key={currentFile} analysis={fileAnalysis} />
          </motion.div>
        ) : (
          <div className="relative -mt-32 z-20 bg-gradient-to-b h-screen flex justify-center items-center from-neutral-200 to-neutral-500 bg-clip-text py-8 text-xl font-bold text-transparent">
            No call graph available.
          </div>
        )}
      </div>
    </div>
  );
}

export default ControlFlow;
