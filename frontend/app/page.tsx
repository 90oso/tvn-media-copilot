"use client";

import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Evidence = {
  evidence_id: string;
  source_type: string;
  source_name: string;
  field: string;
  value: string;
  url?: string | null;
  period?: string | null;
  unit?: string | null;
  scope_note?: string | null;
};
type EvidencePackage = {
  topic?: string | null;
  evidence_state: string;
  independent_provenances: number;
  evidence: Evidence[];
  missing_information: string[];
  contradictions: string[];
};
type HumanReview = { reviewer: string; updated_at: string; state: string; note?: string | null };
type Attention = {
  score: number;
  band: string;
  components: Record<string, number>;
  explanations: Record<string, string>;
  formula: string;
  rules_version: string;
};
type CaseItem = {
  case_id: string;
  news_count: number;
  headline?: string;
  source?: string;
  date?: string | null;
  date_origin?: string | null;
  search_matches?: string[];
  case_languages?: string[];
  evidence_package: EvidencePackage;
  attention: Attention;
  workflow: { state: string; recommended_action: string; draft_enabled: boolean; publication_enabled: boolean; human_review?: HumanReview };
};
type DraftMode = "brief" | "script" | "digital";
type Generated = {
  text: string;
  model: string;
  cached: boolean;
  attempts: number;
  quality?: { citation_coverage?: number; main_text_word_count?: number; estimated_duration_seconds?: number };
  draft?: Record<string, unknown>;
};
type SearchResult = { items: CaseItem[]; total_matches?: number; abstained?: boolean; note?: string };
type IconName = "search" | "arrow" | "refresh" | "sun" | "moon" | "external" | "check" | "alert" | "lock" | "file" | "clock" | "layers" | "copy" | "send" | "chevron" | "spark" | "shield";

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    arrow: <><path d="M5 12h14m-6-6 6 6-6 6"/></>,
    refresh: <><path d="M20 11a8 8 0 1 1-2.2-5.5"/><path d="M20 4v6h-6"/></>,
    sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4m0-14.2-1.4 1.4M6.3 17.7l-1.4 1.4"/></>,
    moon: <path d="M20 16.1A8 8 0 0 1 7.9 4 8 8 0 1 0 20 16.1Z"/>,
    external: <><path d="M14 4h6v6M20 4l-9 9"/><path d="M20 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h6"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    alert: <><path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5m0 3h.01"/></>,
    lock: <><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 1 1 8 0v4"/></>,
    file: <><path d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v5h4M9 13h6M9 17h6"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    layers: <><path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/></>,
    copy: <><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></>,
    send: <><path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/></>,
    chevron: <path d="m7 10 5 5 5-5"/>,
    spark: <><path d="m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5L12 2Z"/></>,
    shield: <><path d="M12 2 4 5v6c0 5.5 3.5 8.5 8 11 4.5-2.5 8-5.5 8-11V5l-8-3Z"/><path d="m8 12 3 3 5-6"/></>,
  };
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

function sourceHeadline(item: CaseItem | null): string {
  if (!item) return "Selecciona un tema";
  return item.headline || item.evidence_package?.evidence?.find(e => e.source_type === "news")?.value || item.case_id;
}
function humanDate(date?: string | null) {
  if (!date) return "Fecha no disponible";
  const d = new Date(date);
  return Number.isNaN(d.getTime()) ? "Fecha no verificada" : new Intl.DateTimeFormat("es-PA", { day: "2-digit", month: "short", year: "numeric", timeZone: "America/Panama" }).format(d);
}
function shortName(x: string) { return x.length > 60 ? `${x.slice(0, 57)}…` : x; }
function isSpanishLanguage(x: string) {
  return ["es", "spa", "es-es", "es-pa", "spanish", "español", "castellano"].includes(x.toLowerCase().trim());
}
function languageName(x: string) {
  const code = x.toLowerCase().trim();
  const labels: Record<string, string> = { es: "español", spa: "español", spanish: "español", "es-es": "español", "es-pa": "español", en: "inglés", eng: "inglés", english: "inglés", ru: "ruso", rus: "ruso", russian: "ruso", fr: "francés", french: "francés", pt: "portugués", portuguese: "portugués" };
  return labels[code] || x;
}
function formatIndicatorValue(value: string) {
  const numeric = Number(value);
  return Number.isFinite(numeric)
    ? new Intl.NumberFormat("es-PA", { maximumFractionDigits: 2 }).format(numeric)
    : value;
}
// Los borradores son copias de trabajo guardadas localmente. El registro de
// aprobación sigue siendo responsabilidad exclusiva de la API de revisiones.
const WORKSPACE_STORAGE_KEY = "tvn-media-copilot:workspace:v1";
const draftStorageKey = (caseId: string) => `tvn-media-copilot:drafts:v1:${caseId}`;
const DRAFT_MODES: DraftMode[] = ["brief", "script", "digital"];

type StoredWorkspace = {
  selectedId: string;
  searchText: string;
  topic: string;
  evidenceFilter: string;
  language: "es" | "all";
  radarMode: "top" | "explore";
  mode: DraftMode;
};

function evidenceSignature(pkg: EvidencePackage): string {
  // Nunca recuperar un borrador si han cambiado sus fuentes o su elegibilidad.
  const idsAndClaims = (pkg.evidence || []).map(e => [
    e.evidence_id, e.source_type, e.source_name, e.field,
    e.value, e.period || "", e.unit || "", e.url || "",
  ]).sort((a, b) => a[0].localeCompare(b[0]));
  return JSON.stringify({
    evidence_state: pkg.evidence_state,
    evidence: idsAndClaims,
    contradictions: [...(pkg.contradictions || [])].sort(),
    missing_information: [...(pkg.missing_information || [])].sort(),
  });
}

function readSavedWorkspace(): StoredWorkspace | null {
  try {
    const raw = localStorage.getItem(WORKSPACE_STORAGE_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as Partial<StoredWorkspace>;
    if (value.language !== "es" && value.language !== "all") return null;
    return {
      selectedId: typeof value.selectedId === "string" ? value.selectedId : "",
      searchText: typeof value.searchText === "string" ? value.searchText : "",
      topic: typeof value.topic === "string" ? value.topic : "",
      evidenceFilter: typeof value.evidenceFilter === "string" ? value.evidenceFilter : "",
      language: value.language,
      radarMode: value.radarMode === "explore" ? "explore" : "top",
      mode: DRAFT_MODES.includes(value.mode as DraftMode) ? value.mode as DraftMode : "brief",
    };
  } catch { return null; }
}

function readSavedDrafts(caseId: string, pkg: EvidencePackage): Partial<Record<DraftMode, Generated>> {
  try {
    const key = draftStorageKey(caseId);
    const raw = localStorage.getItem(key);
    if (!raw) return {};
    const data = JSON.parse(raw) as {
      version?: number;
      signature?: string;
      drafts?: Partial<Record<DraftMode, Generated>>;
    };
    if (data.version !== 1 || data.signature !== evidenceSignature(pkg)) {
      localStorage.removeItem(key);
      return {};
    }
    const result: Partial<Record<DraftMode, Generated>> = {};
    for (const mode of DRAFT_MODES) {
      const item = data.drafts?.[mode];
      if (item && typeof item.text === "string" && typeof item.model === "string") {
        result[mode] = item;
      }
    }
    return result;
  } catch { return {}; }
}

function saveDrafts(caseId: string, pkg: EvidencePackage, drafts: Partial<Record<DraftMode, Generated>>): boolean {
  try {
    localStorage.setItem(draftStorageKey(caseId), JSON.stringify({
      version: 1,
      signature: evidenceSignature(pkg),
      saved_at: new Date().toISOString(),
      drafts,
    }));
    return true;
  } catch { return false; }
}

function errorMessage(error: unknown) { return error instanceof Error ? error.message : "Ocurrió un problema al consultar el sistema."; }
async function jsonResponse<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { cache: "no-store", ...init });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.detail;
    throw new Error((typeof detail === "string" ? detail : detail?.message || detail?.provider_detail) || `Error HTTP ${response.status}`);
  }
  return body as T;
}
function Marker({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "red" | "amber" | "green" }) {
  return <span className={`marker marker-${tone}`}>{children}</span>;
}
function stateTone(value: string): "neutral" | "amber" | "green" {
  return value.includes("suficiente") || value.includes("aprobado") ? "green" : value.includes("parcial") || value.includes("requiere") ? "amber" : "neutral";
}

export default function Home() {
  const [agenda, setAgenda] = useState<CaseItem[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [detail, setDetail] = useState<CaseItem | null>(null);
  const [searchText, setSearchText] = useState("");
  const [topic, setTopic] = useState("");
  const [evidenceFilter, setEvidenceFilter] = useState("");
  const [language, setLanguage] = useState<"es" | "all">("es");
  const [radarMode, setRadarMode] = useState<"top" | "explore">("top");
  const [searchDescription, setSearchDescription] = useState("");
  const [resultTotal, setResultTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isCaseLoading, setIsCaseLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [apiStatus, setApiStatus] = useState<string>("Conectando");
  const [version, setVersion] = useState<string>("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [mode, setMode] = useState<DraftMode>("brief");
  const [drafts, setDrafts] = useState<Partial<Record<DraftMode, Generated>>>({});
  const [reviewer, setReviewer] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [focusedEvidence, setFocusedEvidence] = useState<string>("");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [workspaceReady, setWorkspaceReady] = useState(false);
  const [draftsRestored, setDraftsRestored] = useState(false);
  const detailRequest = useRef(0);
  const searchRequest = useRef(0);
  const evidencePaneRef = useRef<HTMLElement>(null);
  const decisionPaneRef = useRef<HTMLElement>(null);

  const selectCase = useCallback(async (caseId: string) => {
    const request = ++detailRequest.current;
    setSelectedId(caseId);
    // Un nuevo expediente vuelve al principio de su lectura, sin desplazar el radar.
    evidencePaneRef.current?.scrollTo({ top: 0, behavior: "auto" });
    decisionPaneRef.current?.scrollTo({ top: 0, behavior: "auto" });
    setIsCaseLoading(true);
    setError("");
    setNotice("");
    setFocusedEvidence("");
    setDrafts({});
    setDraftsRestored(false);
    try {
      const loaded = await jsonResponse<CaseItem>(`${API}/topics/${encodeURIComponent(caseId)}/analysis`);
      if (request === detailRequest.current) {
        const saved = readSavedDrafts(caseId, loaded.evidence_package);
        setDetail(loaded);
        setDrafts(saved);
        setDraftsRestored(Object.keys(saved).length > 0);
        if (loaded.workflow.human_review?.reviewer) {
          setReviewer(loaded.workflow.human_review.reviewer);
        }
      }
    } catch (e) {
      if (request === detailRequest.current) { setDetail(null); setError(errorMessage(e)); }
    } finally {
      if (request === detailRequest.current) setIsCaseLoading(false);
    }
  }, []);

  const loadRadar = useCallback(async (params?: { query?: string; selectedTopic?: string; selectedEvidence?: string; selectedLanguage?: "es" | "all"; expanded?: boolean }, keepSelected = false) => {
    const request = ++searchRequest.current;
    const q = params?.query?.trim() || "";
    const t = params?.selectedTopic || "";
    const e = params?.selectedEvidence || "";
    const lang = params?.selectedLanguage || "es";
    const explore = !!params?.expanded || !!q || !!t || !!e;
    setIsLoading(true);
    setError("");
    setRadarMode(explore ? "explore" : "top");
    setSearchDescription("");
    try {
      const result = explore
        ? await jsonResponse<SearchResult>(`${API}/explore?${new URLSearchParams({ q, topic: t, evidence: e, language: lang, limit: "30" })}`)
        : await jsonResponse<SearchResult>(`${API}/agenda?${new URLSearchParams({limit: "5", language: lang})}`);
      if (request !== searchRequest.current) return;
      setAgenda(result.items || []);
      setResultTotal(result.total_matches ?? result.items?.length ?? 0);
      setSearchDescription(result.abstained ? (result.note || "No se encontraron resultados en el archivo.") : (explore ? (result.note || "Resultados obtenidos de los titulares y metadatos disponibles.") : "Cinco temas según las reglas de prioridad."));
      if (!keepSelected && result.items?.length) await selectCase(result.items[0].case_id);
      if (!keepSelected && !result.items?.length) { setSelectedId(""); setDetail(null); }
    } catch (e) {
      if (request === searchRequest.current) { setError(errorMessage(e)); setAgenda([]); setResultTotal(0); }
    } finally {
      if (request === searchRequest.current) setIsLoading(false);
    }
  }, [selectCase]);

  useEffect(() => {
    jsonResponse<{ status: string; version?: string }>(`${API}/health`)
      .then(h => { setApiStatus(h.status === "ok" ? "API disponible" : "API con advertencias"); setVersion(h.version || ""); })
      .catch(() => setApiStatus("Servicio no disponible"));

    const saved = readSavedWorkspace();
    if (saved) {
      setSearchText(saved.searchText);
      setTopic(saved.topic);
      setEvidenceFilter(saved.evidenceFilter);
      setLanguage(saved.language);
      setMode(saved.mode);
      setSelectedId(saved.selectedId);
      void (async () => {
        await loadRadar({
          query: saved.radarMode === "explore" ? saved.searchText : "",
          selectedTopic: saved.radarMode === "explore" ? saved.topic : "",
          selectedEvidence: saved.radarMode === "explore" ? saved.evidenceFilter : "",
          selectedLanguage: saved.language,
          expanded: saved.radarMode === "explore",
        }, Boolean(saved.selectedId));
        // No sustituir un expediente investigado por el primer caso del Top 5.
        if (saved.selectedId) await selectCase(saved.selectedId);
      })();
    } else {
      void loadRadar();
    }
    setWorkspaceReady(true);
  }, [loadRadar, selectCase]);

  useEffect(() => {
    if (!workspaceReady) return;
    try {
      localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify({
        selectedId, searchText, topic, evidenceFilter, language, radarMode, mode,
      } satisfies StoredWorkspace));
    } catch { /* Navegación privada o almacenamiento no disponible. */ }
  }, [workspaceReady, selectedId, searchText, topic, evidenceFilter, language, radarMode, mode]);

  const selectedFromRadar = useMemo(() => agenda.find(x => x.case_id === selectedId), [agenda, selectedId]);
  const current = isCaseLoading ? null : (detail || selectedFromRadar);
  const pkg = current?.evidence_package;
  const newsEvidence = useMemo(() => (pkg?.evidence || []).filter(x => x.source_type === "news"), [pkg]);
  const officialEvidence = useMemo(() => (pkg?.evidence || []).filter(x => x.source_type === "official_indicator"), [pkg]);
  const allEvidence = pkg?.evidence || [];
  const focused = allEvidence.find(x => x.evidence_id === focusedEvidence);
  const selectedDraft = drafts[mode];
  const hasDraft = Object.keys(drafts).length > 0;
  const canApprove = Boolean(pkg?.evidence_state === "suficiente para el borrador" && hasDraft && reviewer.trim());

  async function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadRadar({ query: searchText, selectedTopic: topic, selectedEvidence: evidenceFilter, selectedLanguage: language, expanded: true });
  }
  async function generateDraft() {
    if (!detail?.workflow?.draft_enabled) return;
    setIsGenerating(true);
    setError("");
    setNotice("");
    try {
      const caseId = detail.case_id;
      const packageAtStart = detail.evidence_package;
      const request = detailRequest.current;
      const r = await jsonResponse<Generated>(`${API}/generate/${encodeURIComponent(caseId)}?mode=${mode}`, { method: "POST" });
      // Conserva el borrador incluso si se selecciona otra noticia mientras llega Gemini.
      const existing = readSavedDrafts(caseId, packageAtStart);
      const updated = { ...existing, ...drafts, [mode]: r };
      const saved = saveDrafts(caseId, packageAtStart, updated);
      if (request !== detailRequest.current) return;
      setDrafts(updated);
      setDraftsRestored(false);
      setNotice(saved
        ? "Borrador preparado y conservado en este navegador. Debe revisarse antes de aprobarlo."
        : "Borrador preparado, pero el navegador no pudo guardarlo para la próxima visita. Copia el texto antes de salir.");
    } catch (e) { setError(errorMessage(e)); }
    finally { setIsGenerating(false); }
  }
  async function submitReview(action: "approve" | "correct" | "discard") {
    if (!detail || !reviewer.trim()) { setError("Identifica a la persona revisora antes de registrar la decisión."); return; }
    if (action === "approve" && !canApprove) { setError("Genera o recupera un borrador antes de aprobarlo; la evidencia debe ser suficiente."); return; }
    if (action === "correct" && !reviewNote.trim()) { setError("Indica qué debe corregirse."); return; }
    setIsReviewing(true);
    setError("");
    try {
      const body = await jsonResponse<{ review: HumanReview }>(`${API}/reviews/${encodeURIComponent(detail.case_id)}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, reviewer: reviewer.trim(), note: reviewNote.trim() }),
      });
      setReviewNote("");
      setNotice(`Decisión registrada: ${body.review.state}. No se ha publicado ningún contenido.`);
      const loaded = await jsonResponse<CaseItem>(`${API}/topics/${encodeURIComponent(detail.case_id)}/analysis`);
      setDetail(loaded);
      setAgenda(items => items.map(x => x.case_id === detail.case_id ? loaded : x));
    } catch (e) { setError(errorMessage(e)); }
    finally { setIsReviewing(false); }
  }
  async function copyText(value: string) {
    try { await navigator.clipboard.writeText(value); setNotice("Referencia copiada al portapapeles."); }
    catch { setNotice("No se pudo copiar automáticamente. Selecciona el texto para copiarlo."); }
  }

  return (
    <div className="app-shell" data-theme={theme}>
      <header className="masthead">
        <div className="brand-lockup"><div className="brand-symbol" aria-hidden="true">tvn<span>•</span></div><div className="brand-lines"><strong>TVN MEDIA <small> / COPILOTO</small></strong><span>MESA DE REDACCIÓN</span></div></div>
        <nav className="masthead-nav" aria-label="Recorrido editorial"><a className="nav-on" href="#radar">01 · Radar</a><a href="#evidencia">02 · Fuentes</a><a href="#decision">03 · Revisión</a></nav>
        <div className="masthead-actions"><div className="api-indicator" title={version ? `API ${version}` : apiStatus}><span className={apiStatus === "API disponible" ? "online-dot" : "offline-dot"}/>{apiStatus === "API disponible" ? "Sistema disponible" : apiStatus}</div><button className="icon-button theme-toggle" type="button" aria-label={theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"} onClick={() => setTheme(v => v === "light" ? "dark" : "light")}><Icon name={theme === "light" ? "moon" : "sun"}/></button></div>
      </header>

      <main className="main-area">
        <div className="page-intro">
          <div className="intro-main">
            <div className="overline"><span className="overline-line"/> COPILOTO EDITORIAL <span className="intro-version">/ PANAMÁ</span></div>
            <h1>La agenda, <em>bajo análisis.</em></h1>
            <p>Temas priorizados, fuentes para contrastar y borradores sujetos a revisión editorial.</p>
          </div>
          <div className="edition-stamp"><span>ARCHIVO DE TRABAJO</span><strong>Panamá</strong><small>Datos públicos · Sin publicación automática</small></div>
        </div>

        {(error || notice) && <div className={`feedback ${error ? "feedback-error" : "feedback-success"}`} role={error ? "alert" : "status"}><Icon name={error ? "alert" : "check"}/><span>{error || notice}</span><button aria-label="Cerrar aviso" onClick={() => { setError(""); setNotice(""); }}>×</button></div>}

        <div className="workstation">
          <aside id="radar" className="radar-column" aria-label="Radar editorial; desplazamiento independiente" tabIndex={0}>
            <div className="column-caption"><span>01</span><p>RADAR DE NOTICIAS</p><Icon name="layers" size={16}/></div>
            <div className="radar-intro"><h2>¿Qué temas investigar?</h2><p>Explora las noticias y consulta las fuentes de cada expediente.</p></div>
            <form className="search-form" onSubmit={submitSearch}>
              <label className="field-label" htmlFor="editorial-query">BUSCAR TEMAS O TITULARES</label>
              <div className="search-box"><Icon name="search" size={17}/><input id="editorial-query" value={searchText} onChange={e => setSearchText(e.target.value)} placeholder="Empleo, turismo, Canal de Panamá…" maxLength={240}/><button type="submit" aria-label="Buscar eventos" disabled={isLoading}><Icon name="arrow" size={17}/></button></div>
              <div className="filter-row"><label><span>TEMA</span><select value={topic} onChange={e => setTopic(e.target.value)}><option value="">Todas</option><option value="economía">Economía</option><option value="logística">Canal / logística</option><option value="turismo">Turismo</option><option value="servicios públicos">Servicios públicos</option><option value="eventos naturales">Eventos naturales</option><option value="regulación">Regulación</option></select></label><label><span>EVIDENCIA</span><select value={evidenceFilter} onChange={e => setEvidenceFilter(e.target.value)}><option value="">Todos</option><option value="suficiente para el borrador">Suficiente</option><option value="parcial">Parcial</option><option value="insuficiente">Insuficiente</option></select></label></div>
              <label className="language-picker" htmlFor="language-filter"><span><Icon name="layers" size={15}/> Idioma de los titulares</span><select id="language-filter" value={language} onChange={e => { const next = e.target.value as "es" | "all"; setLanguage(next); void loadRadar({ query: searchText, selectedTopic: topic, selectedEvidence: evidenceFilter, selectedLanguage: next, expanded: radarMode === "explore" }); }}><option value="es">Con titulares en español</option><option value="all">Todos los idiomas</option></select></label>
      <button type="submit" className="search-submit" disabled={isLoading}>Buscar eventos <Icon name="arrow" size={15}/></button>
            </form>
            <div className="radar-results-heading"><div><span className="tiny-label">{radarMode === "top" ? "AGENDA PRIORIZADA" : "RESULTADOS DEL CORPUS"}</span><strong>{isLoading ? "Consultando…" : (radarMode === "top" ? "Top 5" : `${resultTotal} coincidencia${resultTotal === 1 ? "" : "s"}`)}</strong></div><button type="button" className="icon-button" title="Actualizar" aria-label="Actualizar agenda" onClick={() => void loadRadar({ query: searchText, selectedTopic: topic, selectedEvidence: evidenceFilter, selectedLanguage: language, expanded: radarMode === "explore" }, true)} disabled={isLoading}><Icon name="refresh" size={17}/></button></div>
            <div className="results-list" aria-live="polite">
              {isLoading && <div className="loading-box"><span className="spinner"/>Consultando el archivo de noticias…</div>}
              {!isLoading && !agenda.length && <div className="empty-radar"><Icon name="search" size={24}/><strong>Sin coincidencias</strong><p>{searchDescription || "Prueba con otros términos o modifica los filtros."}</p><button type="button" onClick={() => { setSearchText(""); setTopic(""); setEvidenceFilter(""); void loadRadar({ selectedLanguage: language }); }}>Volver al Top 5</button></div>}
              {!isLoading && agenda.map((item, index) => {
                const state = item.evidence_package.evidence_state;
                return <button type="button" key={item.case_id} className={`radar-story ${selectedId === item.case_id ? "is-selected" : ""}`} onClick={() => void selectCase(item.case_id)} aria-current={selectedId === item.case_id ? "true" : undefined}>
                  <div className="story-top"><span className="story-number">{String(index + 1).padStart(2, "0")}</span><span className="story-section">{item.evidence_package.topic || "Por clasificar"}</span><span className="story-score">{item.attention.score}<small>/100</small></span></div>
                  <strong>{sourceHeadline(item)}</strong>
                  <div className="story-meta"><span>{item.case_languages?.length && (item.case_languages.length > 1 || (!isSpanishLanguage(item.case_languages[0]))) ? `${item.case_languages.length === 1 ? "Idioma" : "Idiomas"}: ${item.case_languages.map(languageName).join(", ")} · ` : ""}{item.news_count} noticia{item.news_count !== 1 ? "s" : ""}</span><i/> <span className={stateTone(state) === "green" ? "positive-text" : "caution-text"}>{state.includes("suficiente") ? "Borrador permitido" : state}</span></div>
                  <span className="story-case">{item.case_id} <Icon name="arrow" size={13}/></span>
                </button>;
              })}
            </div>
            <div className="radar-footnote"><Icon name="shield" size={16}/><p>El archivo incluye medios internacionales. Los filtros no alteran los titulares ni las fuentes originales.</p></div>
          </aside>

          <section id="evidencia" ref={evidencePaneRef} className="investigation-column" aria-label="Cuaderno de evidencia; desplazamiento independiente" tabIndex={0}>
            <div className="column-caption"><span>02</span><p>FUENTES Y CONTEXTO</p><Icon name="file" size={16}/></div>
            {isCaseLoading && <div className="panel-loading"><span className="spinner"/>Abriendo expediente editorial...</div>}
            {!isCaseLoading && !current && <div className="no-case"><Icon name="layers" size={34}/><h2>Selecciona un tema.</h2><p>Elige un tema del radar o realiza una búsqueda para examinar las fuentes disponibles.</p></div>}
            {!isCaseLoading && current && <>
              <div className="investigation-hero">
                <div className="case-eyebrow"><span>EXPEDIENTE / {current.case_id}</span><Marker tone={stateTone(pkg?.evidence_state || "")}>{pkg?.evidence_state || "Sin evidencia"}</Marker></div>
                <h2>{sourceHeadline(selectedFromRadar || current)}</h2>
                <div className="hero-meta"><span>{pkg?.topic || "Sin tema"}</span><i/> <span>{selectedFromRadar?.source || newsEvidence[0]?.source_name || "Fuente registrada"}</span><i/><span>{selectedFromRadar?.date_origin === "detección" ? "Detectado: " : selectedFromRadar?.date_origin === "publicación" ? "Publicado: " : "Fecha: "}{humanDate(selectedFromRadar?.date)}</span></div>
              </div>
              {selectedFromRadar?.case_languages && selectedFromRadar.case_languages.some(lang => !isSpanishLanguage(lang)) && <div className="language-notice"><Icon name="layers" size={16}/> Este expediente incluye fuentes en <strong>{selectedFromRadar.case_languages.map(languageName).join(", ")}</strong>. Consulta los originales antes de utilizar su contenido.</div>}
              <div className="report-lede"><span>RESUMEN DEL EXPEDIENTE</span><p>Este expediente reúne <strong>{newsEvidence.length} titular{newsEvidence.length !== 1 ? "es" : ""}</strong> y <strong>{officialEvidence.length} indicador{officialEvidence.length !== 1 ? "es" : ""} oficial{officialEvidence.length !== 1 ? "es" : ""}</strong>. Las fuentes reunidas no comprueban por sí solas la veracidad de las afirmaciones.</p></div>
              <div className="investigation-block">
                <div className="block-heading"><div><span className="section-index">A /</span><h3>Qué informan las fuentes</h3></div><span className="block-meta">{newsEvidence.length} titular{newsEvidence.length !== 1 ? "es" : ""}</span></div>
                {newsEvidence.length ? <div className="sources-stack">{newsEvidence.map((e, ix) => <button type="button" key={e.evidence_id} className={`source-record ${focusedEvidence === e.evidence_id ? "source-active" : ""}`} onClick={() => setFocusedEvidence(e.evidence_id)}><div className="source-record-head"><span>FUENTE {String(ix + 1).padStart(2, "0")} · {e.source_name}</span><span className="evidence-code">{e.evidence_id}</span></div><strong>{e.value}</strong><p>{e.scope_note || "Alcance no indicado"}</p><span className="source-record-cta">Seleccionar evidencia <Icon name="arrow" size={13}/></span></button>)}</div> : <p className="empty-inline">No hay titulares registrados en este expediente.</p>}
                <div className="caveat-note"><Icon name="alert" size={17}/><p>Se identificaron {pkg?.independent_provenances ?? 0} procedencias. Esto no demuestra que las investigaciones sean independientes: varios medios pueden reproducir una misma información.</p></div>
              </div>
              <div className="investigation-block">
                <div className="block-heading"><div><span className="section-index">B /</span><h3>Contexto estadístico</h3></div><span className="block-meta">Indicadores oficiales</span></div>
                {officialEvidence.length ? <div className="indicator-grid">{officialEvidence.map(e => <button type="button" key={e.evidence_id} className={`indicator-card ${focusedEvidence === e.evidence_id ? "source-active" : ""}`} onClick={() => setFocusedEvidence(e.evidence_id)}><span>{e.source_name}</span><strong title={`Valor original: ${e.value}`}>{formatIndicatorValue(e.value)} <small>{e.unit || ""}</small></strong><span className="indicator-period">{e.field} · {e.period || "Sin periodo"}</span><p>{e.scope_note}</p><span className="source-record-cta">Ver trazabilidad <Icon name="arrow" size={13}/></span></button>)}</div> : <div className="empty-inline">No se identificó un indicador oficial pertinente para este expediente.</div>}
              </div>
              <div className="investigation-block pending-block">
                <div className="block-heading"><div><span className="section-index">C /</span><h3>Pendientes de verificación</h3></div><span className="block-meta">Antes del borrador</span></div>
                {pkg?.missing_information?.length ? <ul className="pending-list">{pkg.missing_information.map((x, i) => <li key={i}><span>{String(i + 1).padStart(2, "0")}</span>{x}</li>)}</ul> : <div className="empty-inline">El sistema no detectó faltantes específicos. La persona editora debe verificar las fuentes y las afirmaciones.</div>}
                {!!pkg?.contradictions?.length && <div className="conflict-panel"><strong><Icon name="alert" size={17}/> Señales potencialmente contradictorias</strong>{pkg.contradictions.map((c, i) => <p key={i}>{c}</p>)}<small>Detección automática indicativa; no determina qué versión es correcta.</small></div>}
              </div>
              <details className="methodology"><summary><span><Icon name="layers" size={17}/> Cómo se calculó la prioridad</span><span className="method-score">{current.attention.score}/100 <Icon name="chevron" size={15}/></span></summary><p className="formula-note">{current.attention.formula} · {current.attention.rules_version}. Reglas heurísticas propuestas, no medidas de verdad, impacto probado o audiencia.</p>{(["R","I","U","N","E"] as const).map(key => <div className="rule-measure" key={key}><div><strong>{key}</strong><div><span style={{ width: `${Math.max(0, Math.min(1, current.attention.components[key] ?? 0)) * 100}%` }}/></div><span>{Math.round((current.attention.components[key] ?? 0) * 100)}%</span></div><p>{current.attention.explanations[key]}</p></div>)}</details>
            </>}
          </section>

          <aside id="decision" ref={decisionPaneRef} className="decision-column" aria-label="Mesa de decisión editorial; desplazamiento independiente" tabIndex={0}>
            <div className="column-caption"><span>03</span><p>REVISIÓN EDITORIAL</p><Icon name="shield" size={16}/></div>
            {!current ? <div className="decision-empty">Selecciona un caso para habilitar las acciones de revisión.</div> : <>
              <div className="decision-status"><span className="tiny-label">ESTADO DEL EXPEDIENTE</span><h2>{current.workflow.state}</h2><p>{current.workflow.recommended_action}</p><div className="status-line"><span className="status-led"/><strong>Sin publicación automática</strong></div></div>
              <div className="decision-section evidence-focus"><div className="decision-section-title"><span>EVIDENCIA SELECCIONADA</span><Icon name="file" size={16}/></div>{focused ? <><strong>{focused.source_name}</strong><p>{focused.value}</p><div className="focus-code">{focused.evidence_id} · campo: {focused.field}</div><div className="evidence-focus-actions"><button onClick={() => void copyText(`${focused.evidence_id} | ${focused.field} | ${focused.value} | ${focused.url || ""}`)}><Icon name="copy" size={15}/> Copiar referencia</button>{focused.url && <a href={focused.url} target="_blank" rel="noopener noreferrer">Fuente <Icon name="external" size={14}/></a>}</div></> : <p className="focus-placeholder">Selecciona una fuente o un indicador para consultar su identificador y su campo de origen.</p>}</div>
              <div className="decision-section generate-area"><div className="decision-section-title"><span>PREPARACIÓN DEL BORRADOR</span><Icon name="spark" size={17}/></div><div className="draft-tabs" role="tablist" aria-label="Formato editorial">{(["brief","script","digital"] as DraftMode[]).map(m => <button type="button" role="tab" aria-selected={mode === m} className={mode === m ? "tab-active" : ""} onClick={() => setMode(m)} key={m}>{m === "brief" ? "Brief" : m === "script" ? "Guion" : "Digital"}</button>)}</div><div className="format-caption">{mode === "brief" ? "≤250 palabras · enfoque, fuentes y 3 preguntas" : mode === "script" ? "Guion estimado de 45–60 segundos" : "Copy digital de máximo 80 palabras"}</div><button type="button" className="generate-button" onClick={() => void generateDraft()} disabled={!detail?.workflow.draft_enabled || isGenerating}><Icon name={detail?.workflow.draft_enabled ? "spark" : "lock"} size={17}/>{isGenerating ? "Preparando borrador..." : "Preparar borrador"}<Icon name="arrow" size={16}/></button>{!detail?.workflow.draft_enabled && <p className="disabled-explanation">Bloqueado: este caso requiere evidencia adicional.</p>}{selectedDraft && <div className="draft-result"><div className="draft-result-head"><Marker tone="green">{selectedDraft.cached ? "Del caché" : "Generado"}</Marker><span>{selectedDraft.model}</span></div><div className="draft-text">{selectedDraft.text}</div>{selectedDraft.quality && <div className="draft-quality"><span>IDs de citas: {Math.round((selectedDraft.quality.citation_coverage ?? 0) * 100)}% <small>(no acredita sustento semántico)</small></span>{selectedDraft.quality.main_text_word_count != null && <span>Palabras: {selectedDraft.quality.main_text_word_count}</span>}</div>}<button type="button" onClick={() => void copyText(selectedDraft.text)} className="copy-draft"><Icon name="copy" size={14}/> Copiar texto para revisar</button><div className="draft-caveat">Texto asistido: verifica las afirmaciones y las fuentes antes de aprobar.{draftsRestored && <span> Borrador restaurado de este navegador; la decisión editorial se consulta al servidor.</span>}</div></div>}</div>
              <div className="decision-section human-review"><div className="decision-section-title"><span>REVISIÓN HUMANA</span><Icon name="check" size={17}/></div><label htmlFor="reviewer" className="review-label">PERSONA REVISORA</label><input id="reviewer" value={reviewer} onChange={e => setReviewer(e.target.value)} placeholder="Nombre o identificador" maxLength={120}/><label htmlFor="review-note" className="review-label">NOTA EDITORIAL</label><textarea id="review-note" value={reviewNote} onChange={e => setReviewNote(e.target.value)} placeholder="Indica qué información debe comprobarse o corregirse…" maxLength={2000}/><div className="review-buttons"><button type="button" onClick={() => void submitReview("approve")} disabled={!canApprove || isReviewing} className="approve-btn"><Icon name="check" size={16}/> Aprobar borrador</button><button type="button" onClick={() => void submitReview("correct")} disabled={!reviewer.trim() || isReviewing} className="correct-btn">Solicitar corrección</button><button type="button" onClick={() => void submitReview("discard")} disabled={!reviewer.trim() || isReviewing} className="discard-btn">Descartar</button></div>{current.workflow.human_review && <div className="review-record"><span>ÚLTIMO REGISTRO</span><strong>{current.workflow.human_review.state}</strong><small>{current.workflow.human_review.reviewer} · {humanDate(current.workflow.human_review.updated_at)}</small>{current.workflow.human_review.note && <p>{current.workflow.human_review.note}</p>}</div>}<p className="review-disclaimer">Aprobar un borrador no equivale a publicarlo. Antes de aprobar, revisa su contenido y sus fuentes.</p></div>
            </>}
          </aside>
        </div>
        <footer className="page-footer"><span>TVN MEDIA COPILOT · MESA DE REDACCIÓN</span><span>Fuentes públicas · Investigación asistida · Revisión obligatoria</span><span>La repetición de titulares no constituye corroboración independiente.</span></footer>
      </main>
    </div>
  );
}
