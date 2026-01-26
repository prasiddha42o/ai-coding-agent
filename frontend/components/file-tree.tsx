"use client";

import { useState } from "react";
import { ChevronRight, File, Folder, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FileTreeNode as FileTreeNodeType } from "@/types/api";

interface FileTreeProps {
  root: FileTreeNodeType;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}

export function FileTree({ root, selectedPath, onSelect }: FileTreeProps) {
  return (
    <div className="text-sm">
      {(root.children ?? []).map((child) => (
        <FileTreeEntry
          key={child.path}
          node={child}
          depth={0}
          selectedPath={selectedPath}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

function FileTreeEntry({
  node,
  depth,
  selectedPath,
  onSelect,
}: {
  node: FileTreeNodeType;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(depth < 1);
  const indent = { paddingLeft: `${depth * 14 + 8}px` };

  if (node.type === "directory") {
    return (
      <div>
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="hover:bg-muted flex w-full items-center gap-1.5 rounded py-1 text-left"
          style={indent}
        >
          <ChevronRight
            className={cn("size-3.5 shrink-0 transition-transform", isOpen && "rotate-90")}
          />
          {isOpen ? (
            <FolderOpen className="size-3.5 shrink-0" />
          ) : (
            <Folder className="size-3.5 shrink-0" />
          )}
          <span className="truncate">{node.name}</span>
        </button>
        {isOpen && (
          <div>
            {(node.children ?? []).map((child) => (
              <FileTreeEntry
                key={child.path}
                node={child}
                depth={depth + 1}
                selectedPath={selectedPath}
                onSelect={onSelect}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const isSelected = node.path === selectedPath;
  return (
    <button
      type="button"
      onClick={() => onSelect(node.path)}
      className={cn(
        "hover:bg-muted flex w-full items-center gap-1.5 rounded py-1 text-left",
        isSelected && "bg-muted font-medium",
      )}
      style={{ paddingLeft: `${depth * 14 + 8 + 18}px` }}
    >
      <File className="size-3.5 shrink-0" />
      <span className="truncate">{node.name}</span>
    </button>
  );
}
