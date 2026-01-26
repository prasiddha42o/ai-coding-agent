"use client";

import Editor from "@monaco-editor/react";
import { Skeleton } from "@/components/ui/skeleton";

// Maps backend/tools/constants.py's LANGUAGE_EXTENSIONS display names to
// Monaco's language ids.
const MONACO_LANGUAGE: Record<string, string> = {
  Python: "python",
  JavaScript: "javascript",
  TypeScript: "typescript",
  Go: "go",
  Rust: "rust",
  Java: "java",
  Kotlin: "kotlin",
  Ruby: "ruby",
  PHP: "php",
  C: "c",
  "C++": "cpp",
  "C#": "csharp",
  Swift: "swift",
  Scala: "scala",
};

interface CodeEditorProps {
  path: string | null;
  content: string | null;
  language: string | null;
  isLoading: boolean;
}

export function CodeEditor({ path, content, language, isLoading }: CodeEditorProps) {
  if (!path) {
    return (
      <div className="text-muted-foreground flex flex-1 items-center justify-center text-sm">
        Select a file to preview it
      </div>
    );
  }

  if (isLoading || content === null) {
    return (
      <div className="flex flex-1 flex-col gap-2 p-4">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-1/3" />
      </div>
    );
  }

  return (
    <Editor
      key={path}
      height="100%"
      language={language ? MONACO_LANGUAGE[language] : undefined}
      value={content}
      theme="vs-dark"
      options={{
        readOnly: true,
        minimap: { enabled: false },
        fontSize: 13,
        scrollBeyondLastLine: false,
        automaticLayout: true,
      }}
    />
  );
}
