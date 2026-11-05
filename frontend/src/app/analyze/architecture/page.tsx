'use client';
import { GridBackground } from '@/components/GridBackground'
import React from 'react'
import ArchitectureGraph from '@/components/Graph/ArchitectureGraph';
import {motion} from 'framer-motion'

function Architecture() {

  return (
    <div className='h-screen  w-full relative"'>
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
            Architecture Map
          </span> 
        </h1>
      </motion.div>
      <div className=" z-10 h-full w-full">
        <ArchitectureGraph />
      </div>
    </div>
  )
}

export default Architecture