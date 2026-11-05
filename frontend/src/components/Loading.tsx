import React from 'react'
import { GridBackground } from './GridBackground'

function Loading({message}:{message:string}) {
  return (
    <div>
        <GridBackground/>
        <div className="relative z-20 bg-gradient-to-b h-screen flex justify-center items-center from-neutral-200 to-neutral-500 bg-clip-text  text-xl font-bold text-transparent ">
        {message}
      </div>
    </div>
  )
}

export default Loading