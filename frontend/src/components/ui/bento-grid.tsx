import { cn } from "@/lib/utils";
import { ClassInfo, FunctionInfo, GitInfo, ImportInfo, RecentCommit } from "@/types/repo_analysis_type";

export const BentoGrid = ({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) => {
  return (
    <div
      className={cn(
        " grid w-full grid-cols-1 h-[90vh]  gap-4   md:grid-cols-3",
        className,
      )}
    >
      {children}
    </div>
  );
};

export const BentoGridItem = ({
  className,
  title,
  description,
  header,
  icon,
}: {
  className?: string;
  title?: string ;
  description?: string | ImportInfo[] | ClassInfo[] | FunctionInfo[] | GitInfo | React.ReactNode | null;
  header?: React.ReactNode;
  icon?: React.ReactNode;
}) => {
    if(title=="File Summary"){
      const Description = description as string
        return (
          <div
            className={cn(
              "group/bento max-h-[300px] md:max-h-full  custom-scrollbar overflow-y-auto  row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-neutral-700 bg-[#121212] p-4 ",
              className,
            )}
          >
            {header}
            <div className="transition duration-200 group-hover/bento:translate-x-2">
              {icon}
              <div className="text-2xl font-semibold my-2 text-nowrap text-purple-400 ">
                {title}
              </div>
              <div className="font-sans  font-normal text-neutral-600 dark:text-neutral-300 break-words overflow-hidden">
                {Description}
              </div>
            </div>
          </div>
        );
    }else if((title=="Functions" || title=="Classes")&& Array.isArray(description)){
            const Description = (title === "Functions"
          ? description as FunctionInfo[]
          : description as ClassInfo[]
        );
        return (
          <div
            className={cn(
              "group/bento  max-h-[300px] md:max-h-full custom-scrollbar overflow-y-auto  row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-neutral-700 bg-[#121212] p-4 ",
              className,
            )}
          >
            {header}
            <div className="transition duration-200 group-hover/bento:translate-x-2">
              {icon}
              <div className="text-2xl font-semibold my-2 text-nowrap text-purple-400 ">
                {title}
              </div>
              <div className="flex flex-col gap-2">

              {Description?.length === 0 ? (
                  <div className="font-sans  font-normal text-neutral-600 dark:text-neutral-300">
                    No major {title.toLowerCase()}.
                </div>
                ) : (
                    Description?.map((item, idx) => (
                        <div
                        key={idx}
                        className="font-sans font-normal text-neutral-600 dark:text-neutral-300 break-words overflow-hidden"
                        >
                    {item.name}
                    </div>
                ))
            )}
            </div>
            </div>
          </div>
        );
    }else if(title=="Imports" && Array.isArray(description)){
        return (
          <div
            className={cn(
              "group/bento max-h-[300px] md:max-h-full custom-scrollbar overflow-y-auto  row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-neutral-700 bg-[#121212] p-4 ",
              className,
            )}
          >
            {header}
            <div className="transition duration-200 group-hover/bento:translate-x-2">
              {icon}
              <div className="text-2xl font-semibold my-2 text-nowrap text-purple-400 ">
                {title}
              </div>
              <div className="flex flex-col gap-2">

              {
                  description?.map((item, idx)=>{
                      return (
                          <div key={idx} className="font-sans font-normal text-neutral-600 dark:text-neutral-300 break-words overflow-hidden">
                        {
                            item.content 
                        }
                    </div>
                    )
                })
            }
            </div>
            </div>
          </div>
        );
    }else if(title=="File Git History"){
      const gitDescription = description as GitInfo;
        return (
          <div
            className={cn(
              "group/bento max-h-[300px] md:max-h-full  custom-scrollbar overflow-y-auto  row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-neutral-700 bg-[#121212] p-4 ",
              className,
            )}
          >
            {header}
            <div className="transition duration-200 group-hover/bento:translate-x-2">
              {icon}
              <div className="text-2xl font-semibold my-2 text-nowrap text-purple-400 ">
                {title}
              </div>
              <div  className="font-sans font-normal text-neutral-600 dark:text-neutral-300 break-words overflow-hidden">
              <div>Commit Count : <span className="font-bold">{gitDescription.commit_count}</span></div>
              <div>Last modified : <span className="font-bold">{gitDescription.last_modified}</span></div>
              <div><span className="font-bold">Recents commits: </span></div>
              <div className="flex flex-col gap-2">
              {
                gitDescription.recent_commits.map((item:RecentCommit,idx)=>{
                    return(
                        <div className="bg-neutral-900 p-4 rounded-xl shadow-lg w-full h-full border border-neutral-700 text-white overflow-hidden" key={idx}>
                            <div><span className="font-semibold">Author : </span>{item.author}</div>
                            <div><span className="font-semibold">Date : </span> {item.date}</div>
                            <div><span className="font-semibold">Message :</span> {item.message}</div>
                            <div><span className="font-semibold">Commit : </span>{item.sha}</div>
                        </div>
                    )
                })
              }
              </div>
            </div>
            </div>
          </div>
        );
    }
};
