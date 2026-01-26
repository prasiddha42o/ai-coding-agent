import { WorkspaceView } from "@/components/workspace-view";

export default async function RepositoryWorkspacePage({
  params,
}: {
  params: Promise<{ repositoryId: string }>;
}) {
  const { repositoryId } = await params;
  return <WorkspaceView repositoryId={repositoryId} />;
}
