'use client';

import { GridBackground } from '@/components/GridBackground';
import React, { useEffect, useState, Suspense } from 'react';
import { motion } from 'framer-motion';
import { Analysis } from '@/types/repo_analysis_type';
import {
  IconGitBranch,
  IconFileAnalytics,
  IconTopologyStar,
  IconGraph,
  IconHelpCircle,
  IconCode,
  IconRouteSquare2,
  IconHome,
} from "@tabler/icons-react"; 
import { setItem } from '@/utils/indexedDB';
import { useSearchParams } from 'next/navigation';
import axios from 'axios';
import { getAnalysisByIdRoute } from '@/utils/APIRoutes';
import Loading from '@/components/Loading';
import Link from 'next/link';

function AnalyzeContent() {
    const searchParams = useSearchParams();
    const [analysis, setAnalysis] = useState<Analysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>('');

    useEffect(() => {
      const fetchAnalysis = async () => {
        const idParam = searchParams.get('id');
        
        if (!idParam) {
          setError("No analysis ID provided");
          setLoading(false);
          return;
        }

        const repoAnalysisId = parseInt(idParam);

        // Store ID for other pages to use
        sessionStorage.setItem('currentRepoAnalysisId', idParam);

        try {
          const response = await axios.get(getAnalysisByIdRoute(repoAnalysisId));

          const analysisData: Analysis = {
            repo_url: response.data.repo_url,
            branch: response.data.branch,
            repo_analysis: response.data.repo_analysis,
            git_analysis: response.data.git_analysis
          };

          setAnalysis(analysisData);

          // Extract and store file list for UI navigation
          if (analysisData.repo_analysis?.ast) {
            const files = Object.keys(analysisData.repo_analysis.ast);
            await setItem<string[]>("fileList", files);
          }
        } catch (err) {
          console.error("Error fetching analysis:", err);
          setError("Failed to load analysis");
        } finally {
          setLoading(false);
        }
      };

      fetchAnalysis();
    }, [searchParams]);

    if (loading) {
      return <Loading message="Loading analysis..." />;
    }

    if (error) {
      return (
        <div className="min-h-screen bg-black flex items-center justify-center">
          <GridBackground />
          <div className="text-white text-center">
            <p className="text-xl mb-4">{error}</p>
            <Link href="/" className="text-purple-400 underline">Go back home</Link>
          </div>
        </div>
      );
    }

    if (!analysis) {
      return null;
    }

const tabs = [
  {
    title: "Home",
    icon: <IconHome className="w-6 h-6 text-pink-400" />,
    description: "Start your journey here. Search for repositories and begin onboarding effortlessly.",
  },
  {
    title: "Architecture Map",
    icon: <IconTopologyStar className="w-6 h-6 text-pink-400" />,
    description: "Explore the high-level structure of your codebase through an interactive map.",
  },
  {
    title: "Git Analysis",
    icon: <IconGitBranch className="w-6 h-6 text-pink-400" />,
    description: "View commit history, top contributors, frequent changes, and recent activity.",
  },
  {
    title: "File Analysis",
    icon: <IconFileAnalytics className="w-6 h-6 text-pink-400" />,
    description: "Select any file to access key metrics, structural insights, and code-level details.",
  },
  {
    title: "File Graph",
    icon: <IconGraph className="w-6 h-6 text-pink-400" />,
    description: "Visualize relationships between functions and classes within the selected file.",
  },
  {
    title: "Call Graph",
    icon: <IconRouteSquare2 className="w-6 h-6 text-pink-400" />,
    description: "Trace function call flows and control logic for deeper code understanding.",
  },
  {
    title: "Tutorial",
    icon: <IconHelpCircle className="w-6 h-6 text-pink-400" />,
    description: "Follow step-by-step AI-generated tutorials to understand selected files quickly.",
  },
  {
    title: "Assistant",
    icon: <IconCode className="w-6 h-6 text-pink-400" />,
    description: "Ask anything about the codebase and get smart, context-aware answers from AI.",
  },
];


  return (
    <div className="h-screen w-full relative flex flex-col items-center  text-white overflow-auto">
      <div className="fixed h-screen w-full">
      <GridBackground />
      </div>

      {/* Main Welcome Panel */}
      <div className='p-10'>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className=" z-10 max-w-3xl px-6 py-8 bg-neutral-900 backdrop-blur-md rounded-2xl shadow-xl"
        >
        <h1 className="text-3xl lg:text-4xl font-bold mb-4 text-center bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-pink-500 to-red-400">
          <span className='text-white'>Welcome to</span> Into the repo!
        </h1>
        <p className="text-lg text-neutral-300 mb-6 text-center">
          {`Hey! This is your starting point. Here's a quick guide to help you explore this platform effectively:`}
        </p>

        <div className="space-y-4">
          {tabs.map(({ icon, title, description }) => (
            <Step key={title} icon={icon} title={title} description={description} />
          ))}
        </div>

        <p className="mt-6 text-sm text-neutral-400 text-center">
          {`Below, you'll see a floating dock with tabs for each section. Click any tab to jump to that functionality.
          You're all set to begin your journey. 🚀`}
        </p>
      </motion.div>
          </div>
    </div>

    
  );
}

function Step({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="mt-1">{icon}</div>
      <div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="text-neutral-300 text-sm">{description}</p>
      </div>
    </div>
  );
}

function Analyze() {
  return (
    <Suspense fallback={<Loading message="Loading analysis..." />}>
      <AnalyzeContent />
    </Suspense>
  );
}

export default Analyze;
