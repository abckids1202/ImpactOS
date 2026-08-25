import { FormEvent, useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "./api";
import { DEFAULT_MEMBER_PATH, safeNext } from "./auth";
import type { User } from "./types";

function AuthLayout({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children: React.ReactNode }) {
  return <main className="auth-page"><div className="auth-card"><Link className="auth-brand" to="/"><span className="spi-mark">SPI</span><span><strong>Pilar Impact Lab</strong><small>powered by ImpactOS</small></span></Link><div className="public-eyebrow">{eyebrow}</div><h1>{title}</h1><p className="auth-description">{description}</p>{children}<div className="auth-footer"><Link to="/">Back to public site</Link><span>·</span><Link to="/safety-and-privacy">Safety &amp; Privacy</Link></div></div></main>;
}

function AuthError({ error }: { error: unknown }) { return error ? <div className="notice danger auth-error">{error instanceof Error ? error.message : "The request could not be completed."}</div> : null; }

export function MemberLogin({ user, onLogin }: { user: User | null; onLogin: (user: User | null) => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [showDemo, setShowDemo] = useState(false);
  const demo = import.meta.env.DEV && (import.meta.env.VITE_APP_MODE || "DEMO") === "DEMO";
  useEffect(() => { if (demo) setShowDemo(true); }, [demo]);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError(null);
    try { const result = await api.login(email.trim(), password); onLogin(result.user); navigate(safeNext(new URLSearchParams(location.search).get("next")), { replace: true }); }
    catch (err) { setError(err); } finally { setBusy(false); }
  };
  if (user) return <AuthLayout eyebrow="SPI MEMBER ACCESS" title="You are already signed in." description="Continue to the protected ImpactOS workspace." ><div className="auth-actions"><Link className="public-button primary" to={DEFAULT_MEMBER_PATH}>Open Dashboard</Link><button className="public-button secondary" onClick={async () => { await api.logout().catch(() => undefined); onLogin(null); }}>Sign out</button></div></AuthLayout>;
  const fillDemo = (nextEmail: string) => { setEmail(nextEmail); setPassword("demo1234"); setShowDemo(false); };
  return <AuthLayout eyebrow="SPI MEMBER ACCESS" title="Member Login" description="Access is limited to approved SPI members and invited participants."><form className="auth-form" onSubmit={submit}><label>Email<input required type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} /></label><label>Password<div className="password-control"><input required type={showPassword ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? "Hide" : "Show"}</button></div></label><button className="public-button primary auth-submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button></form><AuthError error={error} /><div className="auth-links"><Link to="/forgot-password">Forgot password?</Link><span>New member?</span><Link to="/activate">Activate an SPI account</Link></div>{demo && <div className="demo-access"><button className="demo-toggle" onClick={() => setShowDemo((value) => !value)} type="button">Developer demo access</button>{showDemo && <div className="demo-list">{["student@demo.local", "leader@demo.local", "mentor@demo.local", "osis@demo.local", "moderator@demo.local", "admin@demo.local", "multi@demo.local"].map((demoEmail) => <button type="button" key={demoEmail} onClick={() => fillDemo(demoEmail)}>{demoEmail}</button>)}</div>}</div>}</AuthLayout>;
}

export function ActivatePage({ verificationOnly = false }: { verificationOnly?: boolean }) {
  const location = useLocation();
  const queryToken = new URLSearchParams(location.search).get("token") || "";
  const [token, setToken] = useState(queryToken);
  const [email, setEmail] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  if (queryToken) return <Navigate to={`/invite/${encodeURIComponent(queryToken)}`} replace />;
  const request = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(null); try { const result = await api.requestEmailActivation(email.trim()); setNotice(result.message); } catch (err) { setError(err); } finally { setBusy(false); } };
  if (verificationOnly) return <AuthLayout eyebrow="EMAIL VERIFICATION" title="Check your invitation email." description="Email verification and account activation are completed through a controlled invitation link."><div className="notice">If you have a valid invitation, open the link in that email. For a new activation request, use the form on the activation page.</div><Link className="public-button primary auth-submit" to="/activate">Request activation</Link></AuthLayout>;
  return <AuthLayout eyebrow="CONTROLLED ACTIVATION" title="Activate an SPI account." description="ImpactOS does not use open registration. Accounts are activated through a school invitation or a verified school-email workflow."><div className="auth-section"><h2>Have an invitation?</h2><p>Paste the one-time invitation token from your school or use the full invitation link.</p><label>Invitation token<input value={token} onChange={(event) => setToken(event.target.value)} placeholder="Paste token" /></label><Link className={`public-button primary auth-submit ${!token.trim() ? "disabled-link" : ""}`} to={token.trim() ? `/invite/${encodeURIComponent(token.trim())}` : "#"} aria-disabled={!token.trim()}>Continue with invitation</Link></div><div className="auth-divider"><span>or</span></div><form className="auth-section" onSubmit={request}><h2>Request verified-email activation</h2><p>Enter your school email. The response is intentionally neutral so account eligibility is not disclosed.</p><label>School email<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label><button className="public-button secondary auth-submit" disabled={busy}>{busy ? "Submitting…" : "Request activation"}</button></form><AuthError error={error} />{notice && <div className="notice auth-success">{notice}</div>}</AuthLayout>;
}

export function InvitePage({ onLogin }: { onLogin: (user: User | null) => void }) {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const [preview, setPreview] = useState<any>(null);
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (token) api.invitationPreview(token).then(setPreview).catch(setError); }, [token]);
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(null); try { const result = await api.acceptInvitation(token, { email: preview.email, display_name: displayName.trim(), password, password_confirmation: password, accepted_rules: true }); onLogin(result.user); navigate(DEFAULT_MEMBER_PATH, { replace: true }); } catch (err) { setError(err); } finally { setBusy(false); } };
  if (!preview) return <AuthLayout eyebrow="INVITATION" title="Checking your invitation…" description="The invitation is single-use and expires automatically."><AuthError error={error} />{!error && <div className="loading-inline">Loading invitation details…</div>}<Link className="text-link" to="/activate">Use a different activation route</Link></AuthLayout>;
  return <AuthLayout eyebrow={`INVITATION · ${preview.role}`} title="Create your SPI member account." description={`This invitation is for ${preview.email}. Choose a display name and a strong password to finish activation.`}><form className="auth-form" onSubmit={submit}><label>Display name<input required value={displayName} onChange={(event) => setDisplayName(event.target.value)} autoComplete="name" /></label><label>Password<input required minLength={10} type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" /><small>Use at least 10 characters.</small></label><button className="public-button primary auth-submit" disabled={busy}>{busy ? "Activating…" : "Activate account"}</button></form><AuthError error={error} /></AuthLayout>;
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState(""); const [notice, setNotice] = useState(""); const [error, setError] = useState<unknown>(null); const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(null); try { const result = await api.forgotPassword(email.trim()); setNotice(result.development_reset_token ? `Development reset token: ${result.development_reset_token}` : result.message); } catch (err) { setError(err); } finally { setBusy(false); } };
  return <AuthLayout eyebrow="ACCOUNT RECOVERY" title="Reset your password." description="Enter your member email. The response will not reveal whether an account exists."><form className="auth-form" onSubmit={submit}><label>Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /></label><button className="public-button primary auth-submit" disabled={busy}>{busy ? "Submitting…" : "Request reset"}</button></form><AuthError error={error} />{notice && <div className="notice auth-success">{notice}</div>}<div className="auth-links"><Link to="/login">Return to sign in</Link></div></AuthLayout>;
}

export function ResetPasswordPage() {
  const { token = "" } = useParams(); const navigate = useNavigate(); const [password, setPassword] = useState(""); const [error, setError] = useState<unknown>(null); const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(null); try { await api.resetPassword(token, password); navigate("/login?reset=success", { replace: true }); } catch (err) { setError(err); } finally { setBusy(false); } };
  return <AuthLayout eyebrow="ACCOUNT RECOVERY" title="Choose a new password." description="Use at least 10 characters. Reset links are single-use and expire automatically."><form className="auth-form" onSubmit={submit}><label>New password<input required minLength={10} type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" /></label><button className="public-button primary auth-submit" disabled={busy}>{busy ? "Saving…" : "Save new password"}</button></form><AuthError error={error} /></AuthLayout>;
}

export function ProtectedRoute({ user, checking, children }: { user: User | null; checking: boolean; children: React.ReactNode }) {
  const location = useLocation();
  if (checking) return <div className="loading"><span className="spinner" /> Checking member session…</div>;
  if (!user) { const next = `${location.pathname}${location.search}`; return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />; }
  return <>{children}</>;
}

export function PermissionRoute({ user, permission, children }: { user: User | null; permission: string; children: React.ReactNode }) {
  if (!user) return <Navigate to="/login" replace />;
  if (!(user.permissions || []).includes(permission) && !(permission === "app.access" && user.status === "ACTIVE")) return <Navigate to="/unauthorized" replace />;
  return <>{children}</>;
}

export function UnauthorizedPage() {
  return <AuthLayout eyebrow="ACCESS CONTROL" title="You do not have access to that workspace." description="Your account is signed in, but its active permissions do not include this area. If this looks wrong, ask a school administrator to review your role assignment."><Link className="public-button primary auth-submit" to={DEFAULT_MEMBER_PATH}>Return to workspace</Link></AuthLayout>;
}
