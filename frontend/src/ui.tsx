import React, { FormEvent, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "./api";
import { humanizeStatus } from "./appRoutes";
import type { User } from "./types";

type Theme = "light" | "dark";

function initialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const saved = window.localStorage.getItem("impactos_theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("impactos_theme", theme);
  }, [theme]);
  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

const ThemeContext = React.createContext<{ theme: Theme; setTheme: (theme: Theme) => void } | null>(null);

function useTheme() {
  const context = React.useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used inside ThemeProvider");
  return context;
}

function Icon({ name }: { name: "search" | "sun" | "moon" | "arrow" | "close" }) {
  const paths = {
    search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4 4" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" /></>,
    moon: <path d="M20.4 15.4A8.5 8.5 0 0 1 8.6 3.6 8.5 8.5 0 1 0 20.4 15.4Z" />,
    arrow: <path d="M5 12h13M13 6l6 6-6 6" />,
    close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  }[name];
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths}</svg>;
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  return <button className="utility-button" type="button" aria-label={`Switch to ${next} theme`} aria-pressed={theme === "dark"} onClick={() => setTheme(next)}><Icon name={theme === "dark" ? "sun" : "moon"} /><span className="utility-label">{theme === "dark" ? "Light" : "Dark"}</span></button>;
}

export function OfflineBanner() {
  const [offline, setOffline] = useState(() => typeof navigator !== "undefined" && !navigator.onLine);
  useEffect(() => {
    const online = () => setOffline(false);
    const offlineNow = () => setOffline(true);
    window.addEventListener("online", online);
    window.addEventListener("offline", offlineNow);
    return () => { window.removeEventListener("online", online); window.removeEventListener("offline", offlineNow); };
  }, []);
  return offline ? <div className="offline-banner" role="status"><span className="status-dot" /> You’re offline. Some information may be unavailable, and changes may not be saved.</div> : null;
}

export function BackToTop() {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 520);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  if (!visible) return null;
  return <button className="back-to-top" type="button" aria-label="Back to top" onClick={() => window.scrollTo({ top: 0, behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" })}><Icon name="arrow" /></button>;
}

type SearchResult = { id: string; type: string; label: string; title: string; description: string; status?: string; href: string };

export function SearchDialog() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing = target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.isContentEditable;
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setOpen(true); }
      if (event.key === "/" && !typing) { event.preventDefault(); setOpen(true); }
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!open) return;
    const frame = window.requestAnimationFrame(() => inputRef.current?.focus());
    document.body.classList.add("dialog-open");
    return () => { window.cancelAnimationFrame(frame); document.body.classList.remove("dialog-open"); };
  }, [open]);

  useEffect(() => {
    const value = query.trim();
    if (!open || value.length < 2) { setResults([]); setError(""); setBusy(false); return; }
    setBusy(true); setError("");
    const timer = window.setTimeout(() => {
      api.search(value).then((data) => setResults(data.items as SearchResult[])).catch(() => setError("Search is temporarily unavailable. Try again shortly.")).finally(() => setBusy(false));
    }, 180);
    return () => window.clearTimeout(timer);
  }, [open, query]);

  const go = (href: string) => { setOpen(false); setQuery(""); navigate(href); };
  return <>
    <button className="search-trigger" type="button" aria-label="Search workspace" onClick={() => setOpen(true)}><Icon name="search" /><span>Search workspace</span><kbd>⌘ K</kbd></button>
    {open && <div className="dialog-backdrop" role="presentation" onMouseDown={() => setOpen(false)}><section className="search-dialog" role="dialog" aria-modal="true" aria-labelledby="search-dialog-title" onMouseDown={(event) => event.stopPropagation()}><div className="search-dialog-heading"><div><span className="eyebrow">FIND A RECORD</span><h2 id="search-dialog-title">Search your workspace</h2></div><button className="dialog-close" type="button" aria-label="Close search" onClick={() => setOpen(false)}><Icon name="close" /></button></div><label className="search-dialog-input"><Icon name="search" /><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Problems, reports, research, projects, tasks…" autoComplete="off" /></label><div className="search-results" aria-live="polite">{busy && <div className="search-message"><span className="spinner" /> Searching authorized records…</div>}{!busy && error && <div className="search-message danger-copy">{error}</div>}{!busy && !error && query.trim().length < 2 && <div className="search-message">Type at least two characters. Results respect your active school permissions.</div>}{!busy && !error && query.trim().length >= 2 && !results.length && <div className="search-message">No authorized records match “{query.trim()}”.</div>}{!busy && results.map((item) => <button className="search-result" type="button" key={`${item.type}-${item.id}`} onClick={() => go(item.href)}><span className={`result-icon result-${item.type}`}><Icon name={item.type === "task" ? "arrow" : item.type === "problem" ? "search" : "arrow"} /></span><span className="result-copy"><small>{item.label}</small><strong>{item.title}</strong><span>{item.description}</span></span>{item.status && <span className="result-status">{humanizeStatus(item.status)}</span>}</button>)}</div><div className="search-dialog-footer"><span><kbd>Esc</kbd> close</span><span><kbd>↵</kbd> open result</span></div></section></div>}
  </>;
}

export function FeedbackButton({ user }: { user: User }) {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState("CONFUSING");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState("MEDIUM");
  const [allowContact, setAllowContact] = useState(false);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await api.feedback({ category, description, severity, allow_contact: allowContact, route: location.pathname, user_role: (user.roles || [user.role]).join(", "), browser: navigator.userAgent.slice(0, 120), screen_size: `${window.innerWidth}x${window.innerHeight}`, app_version: "0.1.0" });
      setSent(true); setDescription("");
    } catch (err) { setError(err instanceof Error ? err.message : "Feedback could not be sent."); } finally { setBusy(false); }
  };
  return <><button className="feedback-trigger" type="button" onClick={() => { setOpen(true); setSent(false); }}><span aria-hidden="true">↯</span><span>Send feedback</span></button>{open && <div className="dialog-backdrop" role="presentation" onMouseDown={() => setOpen(false)}><section className="feedback-dialog" role="dialog" aria-modal="true" aria-labelledby="feedback-title" onMouseDown={(event) => event.stopPropagation()}><div className="search-dialog-heading"><div><span className="eyebrow">HELP IMPROVE IMPACTOS</span><h2 id="feedback-title">Send feedback</h2></div><button className="dialog-close" type="button" aria-label="Close feedback" onClick={() => setOpen(false)}><Icon name="close" /></button></div>{sent ? <div className="feedback-success"><div className="success-mark">✓</div><h3>Thank you for helping us improve.</h3><p>Your feedback was sent without including private report content or session details.</p><button className="button primary" type="button" onClick={() => setOpen(false)}>Close</button></div> : <form className="feedback-form" onSubmit={submit}><label>What would you like to tell us?<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="BROKEN">Something is broken</option><option value="CONFUSING">Something is confusing</option><option value="SUGGESTION">Feature suggestion</option><option value="ACCESSIBILITY">Accessibility issue</option><option value="OTHER">Other</option></select></label><label>Your description<textarea required minLength={10} maxLength={4000} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Tell us what happened or what would make this clearer." /></label><div className="form-two"><label>Severity<select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option></select></label><label className="checkbox-label"><input type="checkbox" checked={allowContact} onChange={(event) => setAllowContact(event.target.checked)} /> It’s okay to contact me about this</label></div><p className="field-help">We include only safe context: the current page, role, browser, screen size, and app version. Never passwords, private records, or session tokens.</p>{error && <div className="notice danger">{error}</div>}<button className="button primary" type="submit" disabled={busy}>{busy ? "Sending…" : "Send feedback"}</button></form>}</section></div>}</>;
}

export function GlobalUtilities({ user }: { user: User | null }) {
  return <><OfflineBanner /><BackToTop />{user && <div className="utility-dock"><ThemeToggle /><SearchDialog /><FeedbackButton user={user} /></div>}</>;
}
