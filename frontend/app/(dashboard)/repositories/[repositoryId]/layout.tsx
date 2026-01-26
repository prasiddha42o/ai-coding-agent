import { RepositoryHeader } from "@/components/repository-header";

export default async function RepositoryLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ repositoryId: string }>;
}) {
  const { repositoryId } = await params;

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <RepositoryHeader repositoryId={repositoryId} />
      <div className="flex flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
