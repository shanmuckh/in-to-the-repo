'use client';
import { GridBackground } from '@/components/GridBackground';
import React, { useEffect, useState } from 'react';
import { FileCodeViewer } from '@/components/FileAnalysis/FileCodeViewer';
import { Analysis } from '@/components/FileAnalysis/Analysis';
import Loading from '@/components/Loading';
import { motion } from 'framer-motion';
import { FileAnalysis as file_analysis } from '@/types/file_analysis_type';
import { Analysis as repo_analysis, ASTFileData } from '@/types/repo_analysis_type';
import FileSelector from '@/components/FileAnalysis/FileSelector';
import { getItem } from '@/utils/indexedDB';
import axios from 'axios';
import { getAnalysisByIdRoute } from '@/utils/APIRoutes';

function FileAnalysis() {
  const [fileAnalysis, setFileAnalysis] = useState<file_analysis | null>(null);
  const [currentFile, setCurrentFile] = useState<string>("Choose a file to view its analysis.");
  const [AST, setAST] = useState<ASTFileData | null>(null);
  const [analysis, setAnalysis] = useState<repo_analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCodeViewer, setShowCodeViewer] = useState(false);

  useEffect(() => {
    async function fetchFileAnalysis() {
      // Get repo_analysis_id from session
      const repoAnalysisId = sessionStorage.getItem('currentRepoAnalysisId');
      if (!repoAnalysisId) {
        console.error("[FILE-ANALYSIS] No repo_analysis_id in session");
        setLoading(false);
        return;
      }

      try {
        // Fetch analysis from API
        const response = await axios.get(getAnalysisByIdRoute(parseInt(repoAnalysisId)));
        const analysisData: repo_analysis = {
          repo_url: response.data.repo_url,
          branch: response.data.branch,
          repo_analysis: response.data.repo_analysis,
          git_analysis: response.data.git_analysis
        };
        setAnalysis(analysisData);

        // Get last used file from IndexedDB (UI state)
        const file = await getItem<string>("lastUsedFile");
        if (!file) {
          setLoading(false);
          return;
        }

        const astForFile = analysisData?.repo_analysis?.ast?.[file];
        setCurrentFile(file);
        if (astForFile) {
          setAST(astForFile);
        } else {
          console.warn("AST not found for file:", file);
        }

        // Check if we have cached file analysis (on-demand AI analysis)
        const storageKey = `fileAnalysis-${file}`;
        const file_analysis = await getItem<file_analysis>(storageKey);
        if (file_analysis) {
          setFileAnalysis(file_analysis);
        }
      } catch (err) {
        console.error("[FILE-ANALYSIS] Error fetching analysis:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchFileAnalysis();
  }, []);

  if (loading) return <div><Loading message={"Retrieving file analysis..."} /></div>;

  return (
    <div className='h-screen flex flex-col overflow-y-auto items-center w-full relative scroll-smooth'>
      {/* Background Grid */}
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
            File Analysis:
          </span> 
        </h1>
        <FileSelector  selectedFile={currentFile} onFileSelect={()=>{window.location.reload()}}/>
      </motion.div>


    {fileAnalysis && AST ? (    
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

      {/* Main Content */}
      <motion.div
        className="z-20 md:h-[80vh] flex flex-col md:flex-row p-8 pt-0 w-full gap-4 justify-center items-center"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Analysis Section */}
        <motion.div
          className="z-10 w-full h-full flex justify-center items-center"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {(fileAnalysis && AST) &&
          <Analysis fileAnalysis={fileAnalysis?.analysis} AST={AST} />
          }
        </motion.div>

        {/* File Code Viewer - Desktop View */}
        <div className="hidden lg:flex max-w-xl h-full justify-center items-center w-full">
        {fileAnalysis && (
          <FileCodeViewer
            filename={currentFile}
            language={fileAnalysis?.analysis.language}
            code={fileAnalysis?.analysis.code}
          />)
        }
        </div>
      </motion.div>

      {/* File Code Viewer - Mobile Slide-in Drawer */}
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
        {
          fileAnalysis && (
        <FileCodeViewer
          filename={currentFile}
          language={fileAnalysis?.analysis.language}
          code={fileAnalysis?.analysis.code}
        />
          )
        }
      </motion.div>
      </>
      ) : (
          <div className="relative -mt-32 z-20 bg-gradient-to-b h-screen flex justify-center items-center from-neutral-200 to-neutral-500 bg-clip-text py-8 text-xl font-bold text-transparent">
            No file analysis available.
          </div>
)}
    </div>
  );
}

export default FileAnalysis;
