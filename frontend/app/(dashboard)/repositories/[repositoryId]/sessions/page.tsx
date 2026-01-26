import { SessionsListView } from "@/components/sessions-list-view";

export default async function SessionsPage({
  params,
}: {
  params: Promise<{ repositoryId: string }>;
}) {
  const { repositoryId } = await params;
  return <SessionsListView repositoryId={repositoryId} />;
}
