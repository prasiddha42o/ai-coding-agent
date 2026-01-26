/**
 * TypeScript mirrors of the backend's Pydantic schemas (backend/schemas/*.py).
 * Kept as one file since the two sides aren't code-generated from a shared
 * source of truth — if you change a backend schema, update this by hand.
 */

export type RepositorySourceType = "github" | "zip";
export type RepositoryStatus = "pending" | "cloning" | "indexing" | "ready" | "error";
export type SessionStatus = "active" | "completed" | "failed";
export type ComplexityLevel = "trivial" | "moderate" | "complex";
export type PlanStatus =
  | "pending_approval"
  | "approved"
  | "rejected"
  | "executing"
  | "completed"
  | "failed";
export type ChangeType = "create" | "modify" | "delete";
export type ChangeStatus = "proposed" | "applied" | "reverted";
export type TestRunner = "pytest" | "jest" | "npm" | "unknown";
export type TestStatus = "passed" | "failed" | "error" | "skipped";
export type CommitStatus = "draft" | "committed";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RepositoryMetadata {
  language?: string | null;
  framework?: string | null;
  build_tool?: string | null;
  package_manager?: string | null;
  dependency_files?: string[];
  config_files?: string[];
  folder_hierarchy?: string[];
}

export interface Repository {
  id: string;
  name: string;
  source_type: RepositorySourceType;
  source_url: string | null;
  default_branch: string;
  status: RepositoryStatus;
  error_message: string | null;
  // `{}` before the metadata-extraction pass completes — every field optional.
  metadata_json: RepositoryMetadata;
  last_indexed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  language: string | null;
  children: FileTreeNode[] | null;
}

export interface FileContent {
  path: string;
  content: string;
  language: string | null;
}

export interface GraphSymbol {
  kind: string;
  name: string;
  start_line: number;
  end_line: number;
}

export interface GraphNode {
  id: string;
  file_path: string;
  language: string | null;
  symbols: GraphSymbol[];
}

export interface GraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: string;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CodingSession {
  id: string;
  repository_id: string;
  user_id: string;
  title: string | null;
  status: SessionStatus;
  created_at: string;
  completed_at: string | null;
}

export interface PlanStep {
  title: string;
  description: string;
  affected_files: string[];
}

export interface Plan {
  id: string;
  session_id: string;
  user_prompt: string;
  summary: string | null;
  status: PlanStatus;
  complexity: ComplexityLevel;
  steps: PlanStep[];
  affected_files: string[];
  approved_at: string | null;
  rejected_at: string | null;
  created_at: string;
}

export interface ReviewNote {
  severity: string;
  message: string;
  line: number | null;
}

export interface Change {
  id: string;
  plan_id: string;
  file_path: string;
  change_type: ChangeType;
  status: ChangeStatus;
  diff: string | null;
  explanation: string | null;
  review_notes: ReviewNote[] | null;
}

export interface StackTraceEntry {
  test_name: string;
  message: string;
  trace: string | null;
}

export interface TestRun {
  id: string;
  session_id: string;
  runner: TestRunner;
  command: string;
  status: TestStatus;
  passed_count: number;
  failed_count: number;
  skipped_count: number;
  duration_ms: number;
  output: string | null;
  stack_traces: StackTraceEntry[];
  created_at: string;
}

export interface Commit {
  id: string;
  session_id: string;
  message: string;
  diff_summary: string | null;
  branch: string;
  sha: string | null;
  status: CommitStatus;
}

export interface ReviewResponse {
  summary: string;
  changes: Change[];
}

/** One event from the streamed POST /plans/{id}/run pipeline. */
export interface PipelineEvent {
  stage: "code_generation" | "review" | "apply" | "testing" | "commit" | "pipeline";
  status: "started" | "completed" | "error" | "awaiting_decision";
  message?: string;
  summary?: string;
  changes?: Change[];
  test_run?: TestRun;
  commit?: Commit;
}
