import React from "react";
import { BentoGrid, BentoGridItem } from "../ui/bento-grid";
import {
  IconFileImport,        // For Imports
  IconFunction,          // For Functions
  IconBraces,            // For Classes
  IconFileTextAi,        // For File Summary
  IconGitCommit,         // For Git History
} from "@tabler/icons-react";
import { FileAnalysis } from "@/types/file_analysis_type";
import { ASTFileData } from "@/types/repo_analysis_type";


export function Analysis({fileAnalysis,AST}:{fileAnalysis:FileAnalysis["analysis"], AST:ASTFileData}) {
const items = [
  {
    title: "Imports",
    description: AST?.imports,
    icon: <IconFileImport className="h-4 w-4 text-neutral-500" />,
  },
  {
    title: "Functions",
    description: AST?.functions,
    icon: <IconFunction className="h-4 w-4 text-neutral-500" />,
  },
  {
    title: "Classes",
    description: AST?.classes,
    icon: <IconBraces className="h-4 w-4 text-neutral-500" />,
  },
  {
    title: "File Summary",
    description: fileAnalysis?.error || fileAnalysis?.summary || "No summary available.",
    icon: <IconFileTextAi className="h-4 w-4 text-neutral-500" />,
  },
  {
    title: "File Git History",
    description: AST?.git_info || "No git history available.",
    icon: <IconGitCommit className="h-4 w-4 text-neutral-500" />,
  },
];

  return (
    <BentoGrid className="w-full h-full ">
      {items.map((item, i) => (
        <BentoGridItem
          key={i}
          title={item.title}
          description={item.description}
          icon={item.icon}
          className={i === 3  ? "md:col-span-2" : ""}
        />
      ))}
    </BentoGrid>
  );
}

