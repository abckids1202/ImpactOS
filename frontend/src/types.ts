export type Role = "STUDENT_CONTRIBUTOR" | "STUDENT_PROJECT_LEADER" | "MENTOR" | "OSIS_REVIEWER" | "MODERATOR" | "ADMINISTRATOR" | "STUDENT" | "STUDENT_LEADER" | "OSIS" | "ADMIN";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: Role;
  school_id: string;
  status?: "PENDING" | "ACTIVE" | "DEACTIVATED";
  roles?: string[];
  permissions?: string[];
  membership_id?: string;
  school_name?: string;
}

export interface Cluster {
  id: string;
  title: string;
  summary: string;
  category: string;
  scope: string;
  status: string;
  affected_count: number;
  evidence_count: number;
  report_count: number;
  signal_counts: Record<string, number>;
  reports: Report[];
  evidence: Evidence[];
  official_updates: OfficialUpdate[];
  followed?: boolean;
  priority?: string | null;
  priority_rationale?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Report {
  id: string;
  title: string;
  description: string;
  affected_group: string;
  scope: string;
  category: string;
  visibility: string;
  status: string;
  cluster_id?: string | null;
  author: string;
  sensitivity_reason?: string | null;
}

export interface Evidence {
  id: string;
  source: string;
  type: string;
  observation_date?: string;
  relevance: string;
  visibility: string;
}

export interface OfficialUpdate {
  id: string;
  status: string;
  message: string;
  created_at?: string;
}

export interface Research {
  id: string;
  title: string;
  cluster_id: string;
  leader_id: string;
  mentor_id?: string | null;
  status: string;
  plan: Record<string, unknown>;
  plan_version: number;
  plan_immutable: boolean;
  missing_sections: string[];
}

export interface Metric {
  id: string;
  name: string;
  description: string;
  unit: string;
  direction: string;
  target?: number | null;
  is_primary: boolean;
  observations: Observation[];
  observed_change?: number | null;
  observed_change_percent?: number | null;
}

export interface Observation {
  id: string;
  phase: string;
  value: number;
  observed_on: string;
  sample_size?: number | null;
  notes: string;
}

export interface ImpactProject {
  id: string;
  title: string;
  research_id?: string | null;
  cluster_id: string;
  leader_id: string;
  mentor_id?: string | null;
  status: string;
  target_users: string;
  intervention: string;
  theory_of_change: string;
  risks: string;
  resources: string;
  metrics: Metric[];
  tasks: { id: string; title: string; status: string; priority: string; due_date?: string | null }[];
  report?: Record<string, unknown> | null;
  report_version: number;
}
