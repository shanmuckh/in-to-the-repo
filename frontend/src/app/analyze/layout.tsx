'use client';
import React from "react";
import { FloatingDock } from "@/components/ui/floating-dock";
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
import { UserMenu } from "@/components/UserMenu";

const links = [
  {
    title: "Home",
    icon: <IconHome className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/",
  },
  {
    title: "Architecture Map",
    icon: <IconTopologyStar className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/analyze/architecture",
  },
  {
    title: "Git Analysis",
    icon: <IconGitBranch className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/analyze/commits",
  },{
    title: "File Analysis",
    icon: <IconFileAnalytics className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/analyze/file-analysis",
  },
  {
    title: "File Graph",
    icon: <IconGraph className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/analyze/dependencies",
  },
  {
    title: "Call Graph",
    icon: <IconRouteSquare2 className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/analyze/control-flow",
  },
  {
    title: "Tutorial",
    icon: <IconHelpCircle className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/analyze/tutorial",
  },
  {
    title: "Assistant",
    icon: <IconCode className="h-full w-full text-neutral-500 dark:text-neutral-300" />,
    href: "/analyze/assistant",
  },
];


export default function AnalyzeLayout({
  children,
}: {
  children: React.ReactNode;
}) {


  return (
    <div className="relative overflow-hidden min-h-screen flex flex-col bg-background text-foreground">
      {/* User Menu - Top Right */}
      <div className="absolute top-6 right-6 z-50">
        <UserMenu />
      </div>
      
      <main className="">{children}</main>
      {/* Floating Dock at bottom center */}
      <div className="absolute z-20 bottom-10 w-full flex justify-center">
        <FloatingDock
          mobileClassName="fixed right-5 bottom-10"
          items={links}
        />
      </div>
    </div>
  );
}
