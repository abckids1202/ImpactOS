export const DEFAULT_MEMBER_PATH = "/app/dashboard";

/** Only allow post-login redirects to the protected application namespace. */
export function safeNext(raw: string | null | undefined): string {
  if (!raw) return DEFAULT_MEMBER_PATH;
  let value = raw;
  try { value = decodeURIComponent(raw); } catch { return DEFAULT_MEMBER_PATH; }
  if (!value.startsWith("/app/") || value.startsWith("//") || value.includes("\\") || value.includes(":")) return DEFAULT_MEMBER_PATH;
  return value;
}
