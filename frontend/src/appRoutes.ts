export type AppRouteDefinition = {
  id: string;
  path: string;
  label: string;
  icon: string;
  permission?: string;
  group: "workspace" | "review" | "administration";
  sidebar: boolean;
  mobile: boolean;
};

export const APP_PATHS = {
  app: "/app",
  dashboard: "/app/dashboard",
  problems: "/app/problems",
  newProblem: "/app/problems/new",
  reports: "/app/reports",
  research: "/app/research",
  projects: "/app/projects",
  tasks: "/app/tasks",
  profile: "/app/profile",
  mentor: "/app/mentor",
  mentorReviews: "/app/mentor/reviews",
  osis: "/app/osis",
  osisPriorities: "/app/osis/priorities",
  moderation: "/app/moderation",
  moderationReports: "/app/moderation/reports",
  admin: "/app/admin",
  adminMembers: "/app/admin/members",
  adminInvitations: "/app/admin/invitations",
  adminAudit: "/app/admin/audit",
  notifications: "/app/notifications",
} as const;

export const APP_ROUTES: AppRouteDefinition[] = [
  { id: "dashboard", path: APP_PATHS.dashboard, label: "Dashboard", icon: "⌂", group: "workspace", sidebar: true, mobile: true },
  { id: "problems", path: APP_PATHS.problems, label: "Problems", icon: "◉", permission: "problem.read_public_school", group: "workspace", sidebar: true, mobile: true },
  { id: "reports", path: APP_PATHS.reports, label: "My reports", icon: "▤", permission: "problem_report.create", group: "workspace", sidebar: true, mobile: true },
  { id: "research", path: APP_PATHS.research, label: "Research", icon: "⌁", permission: "research.read_assigned", group: "workspace", sidebar: true, mobile: true },
  { id: "projects", path: APP_PATHS.projects, label: "Impact projects", icon: "↗", permission: "impact.read_assigned", group: "workspace", sidebar: true, mobile: true },
  { id: "tasks", path: APP_PATHS.tasks, label: "My tasks", icon: "✓", permission: "task.read_assigned", group: "workspace", sidebar: true, mobile: true },
  { id: "mentor", path: APP_PATHS.mentor, label: "Review queue", icon: "▣", permission: "mentor.review", group: "review", sidebar: true, mobile: true },
  { id: "osis", path: APP_PATHS.osis, label: "School priorities", icon: "✦", permission: "osis.review", group: "review", sidebar: true, mobile: true },
  { id: "moderation", path: APP_PATHS.moderation, label: "Moderation queue", icon: "⚑", permission: "moderation.review", group: "review", sidebar: true, mobile: true },
  { id: "adminMembers", path: APP_PATHS.adminMembers, label: "Members", icon: "◎", permission: "admin.members.read", group: "administration", sidebar: true, mobile: true },
  { id: "adminInvitations", path: APP_PATHS.adminInvitations, label: "Invitations", icon: "✉", permission: "admin.invitations.manage", group: "administration", sidebar: true, mobile: true },
  { id: "adminAudit", path: APP_PATHS.adminAudit, label: "Audit log", icon: "≡", permission: "admin.audit.read", group: "administration", sidebar: true, mobile: true },
  { id: "profile", path: APP_PATHS.profile, label: "My profile", icon: "◌", permission: "profile.read_own", group: "workspace", sidebar: true, mobile: true },
];

export function visibleAppRoutes(permissions: string[]) {
  return APP_ROUTES.filter((route) => route.sidebar && (!route.permission || permissions.includes(route.permission)));
}

export function humanizeRole(role: string) {
  const labels: Record<string, string> = {
    STUDENT_CONTRIBUTOR: "Student contributor",
    STUDENT_PROJECT_LEADER: "Student project leader",
    MENTOR: "Mentor",
    OSIS_REVIEWER: "OSIS reviewer",
    MODERATOR: "Moderator",
    ADMINISTRATOR: "Administrator",
  };
  return labels[role] || role.replaceAll("_", " ").toLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}

export function humanizeStatus(status: string) {
  const labels: Record<string, string> = {
    SUBMITTED_FOR_REVIEW: "Awaiting review",
    MENTOR_REVIEW: "Awaiting mentor review",
    CHANGES_REQUESTED: "Changes requested",
    RESTRICTED_REVIEW: "Restricted review",
    PRIVATE_REVIEW: "Private review",
    MODERATION_REVIEW: "Awaiting moderation",
    IN_PROGRESS: "In progress",
    TODO: "To do",
    COMPLETED: "Completed",
    VALIDATED: "Validated",
  };
  return labels[status] || status.replaceAll("_", " ").toLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}
