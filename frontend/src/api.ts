const API = import.meta.env.VITE_API_URL || "/api/v1";

function csrfToken(): string {
  return document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith("impactos_csrf="))?.split("=")[1] || "";
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers || {});
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) headers.set("X-CSRF-Token", csrfToken());
  const response = await fetch(`${API}${path}`, { ...init, headers, credentials: "include" });
  const text = await response.text();
  let body: any = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { error: { message: "The server returned an unexpected response." } }; }
  if (!response.ok) {
    const detail = body?.detail;
    let message = body?.error?.message || (typeof detail === "string" ? detail : detail?.message) || "The request could not be completed.";
    if (message === "Not Found") message = "The member service is temporarily unavailable. Please try again.";
    const error = new Error(message) as Error & { code?: string; requestId?: string };
    error.code = body?.error?.code || detail?.code;
    error.requestId = body?.error?.request_id;
    throw error;
  }
  return body as T;
}

export const api = {
  login: (email: string, password: string) => request<{ user: import("./types").User; mode: string; synthetic_data: boolean }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  publicSite: () => request<any>("/public/site"),
  publicFaq: () => request<any[]>("/public/faq"),
  publicImpactStories: (params = "") => request<{ items: any[]; total: number; synthetic_data: boolean }>(`/public/impact-stories${params}`),
  publicImpactStory: (slug: string) => request<any>(`/public/impact-stories/${encodeURIComponent(slug)}`),
  invitationPreview: (token: string) => request<any>(`/auth/invitations/verify?token=${encodeURIComponent(token)}`),
  acceptInvitation: (token: string, payload: Record<string, unknown>) => request<any>(`/auth/activate?token=${encodeURIComponent(token)}`, { method: "POST", body: JSON.stringify(payload) }),
  requestEmailActivation: (email: string) => request<any>("/activation/request-email", { method: "POST", body: JSON.stringify({ email }) }),
  forgotPassword: (email: string) => request<any>("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) }),
  resetPassword: (token: string, password: string) => request<any>("/auth/reset-password", { method: "POST", body: JSON.stringify({ token, password }) }),
  logout: () => request<{ status: string }>("/auth/logout", { method: "POST" }),
  me: async () => {
    const result = await request<any>("/auth/me");
    const membership = result.memberships?.[0];
    const canonicalRole = membership?.roles?.[0] || "STUDENT_CONTRIBUTOR";
    const legacyRole = ({ STUDENT_CONTRIBUTOR: "STUDENT", STUDENT_PROJECT_LEADER: "STUDENT_LEADER", OSIS_REVIEWER: "OSIS", ADMINISTRATOR: "ADMIN" } as Record<string, string>)[canonicalRole] || canonicalRole;
    const role = legacyRole as import("./types").Role;
    return { ...result.user, role, school_id: membership?.school?.id || "", school_name: membership?.school?.name, roles: membership?.roles || [], permissions: membership?.permissions || [], membership_id: membership?.id } as import("./types").User;
  },
  dashboard: (workspace?: string) => request<any>(workspace ? `/dashboard?workspace=${encodeURIComponent(workspace)}` : "/dashboard"),
  clusters: (params = "") => request<import("./types").Cluster[]>(`/problems${params}`),
  cluster: (id: string) => request<import("./types").Cluster>(`/problems/${id}`),
  myReports: () => request<any[]>("/problem-reports/mine"),
  report: (id: string) => request<any>(`/problem-reports/${id}`),
  createReport: (payload: Record<string, unknown>) => request<any>("/problem-reports", { method: "POST", body: JSON.stringify(payload) }),
  submitReport: (id: string) => request<any>(`/problem-reports/${id}/submit`, { method: "POST" }),
  addSignal: (id: string, signal_type: string) => request<import("./types").Cluster>(`/problems/${id}/signals`, { method: "POST", body: JSON.stringify({ signal_type }) }),
  removeSignal: (id: string, signal_type: string) => request<import("./types").Cluster>(`/problems/${id}/signals/${encodeURIComponent(signal_type)}`, { method: "DELETE" }),
  followProblem: (id: string) => request<import("./types").Cluster>(`/problems/${id}/follow`, { method: "POST" }),
  unfollowProblem: (id: string) => request<import("./types").Cluster>(`/problems/${id}/follow`, { method: "DELETE" }),
  addEvidence: (id: string, payload: Record<string, unknown>) => request<import("./types").Cluster>(`/problem-clusters/${id}/evidence`, { method: "POST", body: JSON.stringify(payload) }),
  createResearch: (cluster_id: string, title: string) => request<import("./types").Research>("/research-projects", { method: "POST", body: JSON.stringify({ cluster_id, title }) }),
  research: (id: string) => request<import("./types").Research>(`/research-projects/${id}`),
  researchList: () => request<import("./types").Research[]>("/research-projects"),
  savePlan: (id: string, plan: Record<string, unknown>) => request<import("./types").Research>(`/research-projects/${id}/plan`, { method: "PUT", body: JSON.stringify(plan) }),
  submitResearch: (id: string) => request<import("./types").Research>(`/research-projects/${id}/submit-review`, { method: "POST" }),
  review: (payload: Record<string, unknown>) => request<any>("/reviews", { method: "POST", body: JSON.stringify(payload) }),
  impacts: () => request<import("./types").ImpactProject[]>("/impact-projects"),
  impact: (id: string) => request<import("./types").ImpactProject>(`/impact-projects/${id}`),
  createImpact: (payload: Record<string, unknown>) => request<import("./types").ImpactProject>("/impact-projects", { method: "POST", body: JSON.stringify(payload) }),
  updateImpact: (id: string, payload: Record<string, unknown>) => request<import("./types").ImpactProject>(`/impact-projects/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitImpact: (id: string) => request<import("./types").ImpactProject>(`/impact-projects/${id}/submit-review`, { method: "POST" }),
  addMetric: (id: string, payload: Record<string, unknown>) => request<import("./types").ImpactProject>(`/impact-projects/${id}/metrics`, { method: "POST", body: JSON.stringify(payload) }),
  addObservation: (metricId: string, payload: Record<string, unknown>) => request<import("./types").ImpactProject>(`/impact-metrics/${metricId}/observations`, { method: "POST", body: JSON.stringify(payload) }),
  activate: (id: string) => request<import("./types").ImpactProject>(`/impact-projects/${id}/activate`, { method: "POST" }),
  impactReport: (id: string) => request<any>(`/impact-projects/${id}/report`),
  saveReport: (id: string, content: Record<string, unknown>) => request<any>(`/impact-projects/${id}/report`, { method: "PUT", body: JSON.stringify({ content }) }),
  submitReportForReview: (id: string) => request<any>(`/impact-projects/${id}/submit-report`, { method: "POST" }),
  moderation: () => request<any>("/moderation/queue"),
  moderationReport: (id: string) => request<any>(`/moderation/reports/${id}`),
  moderationDecision: (id: string, decision: string, reason: string) => request<any>(`/moderation/problem-reports/${id}/visibility-decision`, { method: "POST", body: JSON.stringify({ decision, reason }) }),
  moderationAction: (id: string, decision: string, reason: string) => request<any>(`/moderation/reports/${id}/decision`, { method: "POST", body: JSON.stringify({ decision, reason }) }),
  mentorAttention: () => request<any>("/mentor/attention"),
  mentorReviews: () => request<any>("/mentor/reviews"),
  osis: () => request<any>("/osis/overview"),
  osisPriorities: () => request<any>("/osis/priorities"),
  setPriority: (id: string, priority: string, rationale: string) => request<any>(`/osis/problems/${id}/priority`, { method: "POST", body: JSON.stringify({ priority, rationale }) }),
  officialUpdate: (id: string, status: string, message: string) => request<any>(`/problem-clusters/${id}/official-updates`, { method: "POST", body: JSON.stringify({ status, message }) }),
  tasks: (query = "") => request<any>(`/tasks/mine${query}`),
  updateTask: (id: string, status: string) => request<any>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
  adminLogs: () => request<any[]>("/admin/audit-logs"),
  adminAudit: () => request<any[]>("/admin/audit"),
  adminMembers: (query = "") => request<any[]>(`/admin/members${query}`),
  updateMemberRoles: (id: string, roles: string[]) => request<any>(`/admin/members/${id}/roles`, { method: "PATCH", body: JSON.stringify({ roles }) }),
  deactivateMember: (id: string) => request<any>(`/admin/members/${id}/deactivate`, { method: "POST" }),
  reactivateMember: (id: string) => request<any>(`/admin/members/${id}/reactivate`, { method: "POST" }),
  adminInvitations: () => request<any[]>("/admin/invitations"),
  createInvitation: (payload: Record<string, unknown>) => request<any>("/admin/invitations", { method: "POST", body: JSON.stringify(payload) }),
  revokeInvitation: (id: string) => request<any>(`/admin/invitations/${id}/revoke`, { method: "POST" }),
  resendInvitation: (id: string) => request<any>(`/admin/invitations/${id}/resend`, { method: "POST" }),
  createPublicStory: (payload: Record<string, unknown>) => request<any>("/admin/public-impact-stories", { method: "POST", body: JSON.stringify(payload) }),
  publicStoryAction: (id: string, action: "submit-review" | "approve" | "publish" | "withdraw") => request<any>(`/admin/public-impact-stories/${id}/${action}`, { method: "POST" }),
  notifications: () => request<any[]>("/notifications"),
};
