"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useImportGithubRepository, useImportZipRepository } from "@/hooks/use-repositories";
import { ApiError } from "@/services/api-client";

export function ImportRepositoryDialog() {
  const [open, setOpen] = useState(false);
  const [githubUrl, setGithubUrl] = useState("");
  const [githubBranch, setGithubBranch] = useState("");
  const [githubName, setGithubName] = useState("");
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [zipName, setZipName] = useState("");

  const importGithub = useImportGithubRepository();
  const importZip = useImportZipRepository();

  function resetAndClose() {
    setOpen(false);
    setGithubUrl("");
    setGithubBranch("");
    setGithubName("");
    setZipFile(null);
    setZipName("");
  }

  async function handleGithubSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await importGithub.mutateAsync({
        sourceUrl: githubUrl.trim(),
        name: githubName.trim() || null,
        branch: githubBranch.trim() || null,
      });
      toast.success("Import started — indexing runs in the background.");
      resetAndClose();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Couldn't import that repository.");
    }
  }

  async function handleZipSubmit(event: FormEvent) {
    event.preventDefault();
    if (!zipFile) {
      toast.error("Choose a .zip file first.");
      return;
    }
    try {
      await importZip.mutateAsync({ file: zipFile, name: zipName.trim() || null });
      toast.success("Import started — indexing runs in the background.");
      resetAndClose();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Couldn't import that archive.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button>Import repository</Button>} />
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Import a repository</DialogTitle>
          <DialogDescription>
            Connect a public GitHub repository or upload a ZIP archive of your project.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="github">
          <TabsList className="w-full">
            <TabsTrigger value="github" className="flex-1">
              GitHub
            </TabsTrigger>
            <TabsTrigger value="zip" className="flex-1">
              Upload ZIP
            </TabsTrigger>
          </TabsList>

          <TabsContent value="github">
            <form onSubmit={handleGithubSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="github-url">Repository URL</Label>
                <Input
                  id="github-url"
                  placeholder="https://github.com/owner/repo"
                  required
                  value={githubUrl}
                  onChange={(event) => setGithubUrl(event.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="github-branch">Branch (optional)</Label>
                  <Input
                    id="github-branch"
                    placeholder="main"
                    value={githubBranch}
                    onChange={(event) => setGithubBranch(event.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="github-name">Name (optional)</Label>
                  <Input
                    id="github-name"
                    placeholder="Defaults to repo name"
                    value={githubName}
                    onChange={(event) => setGithubName(event.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={importGithub.isPending}>
                  {importGithub.isPending ? "Importing…" : "Import from GitHub"}
                </Button>
              </DialogFooter>
            </form>
          </TabsContent>

          <TabsContent value="zip">
            <form onSubmit={handleZipSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="zip-file">Archive</Label>
                <Input
                  id="zip-file"
                  type="file"
                  accept=".zip"
                  required
                  onChange={(event) => setZipFile(event.target.files?.[0] ?? null)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="zip-name">Name (optional)</Label>
                <Input
                  id="zip-name"
                  placeholder="Defaults to the archive's file name"
                  value={zipName}
                  onChange={(event) => setZipName(event.target.value)}
                />
              </div>
              <DialogFooter>
                <Button type="submit" disabled={importZip.isPending}>
                  {importZip.isPending ? "Uploading…" : "Import ZIP"}
                </Button>
              </DialogFooter>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
