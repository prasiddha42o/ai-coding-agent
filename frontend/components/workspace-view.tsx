"use client";

import { useState } from "react";
import { AgentPanel } from "@/components/agent-panel";
import { CodeEditor } from "@/components/code-editor";
import { FileTree } from "@/components/file-tree";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useFileContent, useFileTree } from "@/hooks/use-files";

export function WorkspaceView({ repositoryId }: { repositoryId: string }) {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const { data: tree, isLoading: isTreeLoading, isError: isTreeError } = useFileTree(repositoryId);
  const { data: fileContent, isLoading: isContentLoading } = useFileContent(
    repositoryId,
    selectedPath,
  );

  return (
    <>
      <aside className="border-border/60 w-64 shrink-0 border-r">
        <ScrollArea className="h-full">
          <div className="p-2">
            {isTreeLoading && (
              <p className="text-muted-foreground px-2 py-1 text-xs">Loading files…</p>
            )}
            {isTreeError && (
              <p className="text-destructive px-2 py-1 text-xs">Couldn&apos;t load the file tree.</p>
            )}
            {tree && <FileTree root={tree} selectedPath={selectedPath} onSelect={setSelectedPath} />}
          </div>
        </ScrollArea>
      </aside>
      <div className="flex flex-1 flex-col overflow-hidden">
        <CodeEditor
          path={selectedPath}
          content={fileContent?.content ?? null}
          language={fileContent?.language ?? null}
          isLoading={isContentLoading}
        />
      </div>
      <AgentPanel repositoryId={repositoryId} />
    </>
  );
}
