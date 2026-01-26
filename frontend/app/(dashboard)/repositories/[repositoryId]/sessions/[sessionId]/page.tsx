import { SessionDetailView } from "@/components/session-detail-view";

export default async function SessionDetailPage({
  params,
}: {
  params: Promise<{ repositoryId: string; sessionId: string }>;
}) {
  const { sessionId } = await params;
  return <SessionDetailView sessionId={sessionId} />;
}
