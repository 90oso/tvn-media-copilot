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
  const detailRequest = useRef(0);
  const searchRequest = useRef(0);

  const selectCase = useCallback(async (caseId: string) => {
    const request = ++detailRequest.current;
    setSelectedId(caseId);
    setIsCaseLoading(true);
    setError("");
    setNotice("");
    setFocusedEvidence("");
    setDrafts({});
    try {
      const loaded = await jsonResponse<CaseItem>(`${API}/topics/${encodeURIComponent(caseId)}/analysis`);
      if (request === detailRequest.current) setDetail(loaded);
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
      setSearchDescription(result.abstained ? (result.note || "Sin evidencia suficiente en el corpus.") : (explore ? (result.note || "Coincidencias del snapshot.") : "Cinco señales según prioridad de atención."));
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
      .catch(() => setApiStatus("API desconectada"));
    void loadRadar();
  }, [loadRadar]);

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
      const r = await jsonResponse<Generated>(`${API}/generate/${encodeURIComponent(detail.case_id)}?mode=${mode}`, { method: "POST" });
      setDrafts(previous => ({ ...previous, [mode]: r }));
      setNotice(r.cached ? "Se recuperó un borrador validado del cache." : "Borrador preparado. Pendiente de revisión humana.");
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
    try { await navigator.clipboard.writeText(value); setNotice("Copiado al portapapeles."); }
    catch { setNotice("No se pudo copiar automáticamente. Selecciona el texto para copiarlo."); }
  }

  return (
    <div className="app-shell" data-theme={theme}>
      <header className="masthead">
        <div className="brand-lockup"><div className="brand-symbol" aria-hidden="true">tvn<span>•</span></div><div className="brand-lines"><strong>TVN MEDIA <small> / COPILOT</small></strong><span>MESA DE REDACCIÓN DIGITAL</span></div></div>
        <nav className="masthead-nav" aria-label="Recorrido editorial"><a className="nav-on" href="#radar">01 · Radar</a><a href="#evidencia">02 · Evidencia</a><a href="#decision">03 · Decisión</a></nav>
        <div className="masthead-actions"><div className="api-indicator" title={version ? `API ${version}` : apiStatus}><span className={apiStatus === "API disponible" ? "online-dot" : "offline-dot"}/>{apiStatus}</div><button className="icon-button theme-toggle" type="button" aria-label={theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"} onClick={() => setTheme(v => v === "light" ? "dark" : "light")}><Icon name={theme === "light" ? "moon" : "sun"}/></button></div>
      </header>

      <main className="main-area">
        <div className="page-intro">
          <div className="intro-main"><div className="overline"><span className="overline-line"/> DE LA SEÑAL A LA DECISIÓN <span className="intro-version">/ MESA DE REDACCIÓN</span></div><h1>Del dato a la historia.<br/><em>De la señal a la decisión.</em></h1><p>Una señal merece atención. La evidencia determina qué podemos afirmar. La decisión siempre es humana.</p></div>
          <div className="edition-stamp"><span>EDICIÓN DE TRABAJO</span><strong>Panamá</strong><small>Corpus público congelado<br/>Sin publicación automática</small><span className="stamp-hairline"/></div>
        </div>

        {(error || notice) && <div className={`feedback ${error ? "feedback-error" : "feedback-success"}`} role={error ? "alert" : "status"}><Icon name={error ? "alert" : "check"}/><span>{error || notice}</span><button aria-label="Cerrar aviso" onClick={() => { setError(""); setNotice(""); }}>×</button></div>}

        <div className="workstation">
          <aside id="radar" className="radar-column" aria-label="Radar editorial">
            <div className="column-caption"><span>01</span><p>RADAR DE TEMAS</p><Icon name="layers" size={16}/></div>
            <div className="radar-intro"><h2>Qué investigar <em>ahora.</em></h2><p>Busca por hechos o explora las señales clasificadas en el corpus.</p></div>
            <form className="search-form" onSubmit={submitSearch}>
              <label className="field-label" htmlFor="editorial-query">CONSULTA EN ESPAÑOL</label>
              <div className="search-box"><Icon name="search" size={17}/><input id="editorial-query" value={searchText} onChange={e => setSearchText(e.target.value)} placeholder="Ej. empleo, turismo, Canal..." maxLength={240}/><button type="submit" aria-label="Buscar eventos" disabled={isLoading}><Icon name="arrow" size={17}/></button></div>
              <div className="filter-row"><label><span>SECCIÓN</span><select value={topic} onChange={e => setTopic(e.target.value)}><option value="">Todas</option><option value="economía">Economía</option><option value="logística">Canal / logística</option><option value="turismo">Turismo</option><option value="servicios públicos">Servicios públicos</option><option value="eventos naturales">Eventos naturales</option><option value="regulación">Regulación</option></select></label><label><span>EVIDENCIA</span><select value={evidenceFilter} onChange={e => setEvidenceFilter(e.target.value)}><option value="">Todos</option><option value="suficiente para el borrador">Suficiente</option><option value="parcial">Parcial</option><option value="insuficiente">Insuficiente</option></select></label></div>
              <label className="language-picker" htmlFor="language-filter"><span><Icon name="layers" size={15}/> Idioma del radar</span><select id="language-filter" value={language} onChange={e => { const next = e.target.value as "es" | "all"; setLanguage(next); void loadRadar({ query: searchText, selectedTopic: topic, selectedEvidence: evidenceFilter, selectedLanguage: next, expanded: radarMode === "explore" }); }}><option value="es">Titulares en español</option><option value="all">Todos los idiomas</option></select></label>
      <button type="submit" className="search-submit" disabled={isLoading}>Explorar corpus <Icon name="arrow" size={15}/></button>
            </form>
            <div className="radar-results-heading"><div><span className="tiny-label">{radarMode === "top" ? "AGENDA PRIORIZADA" : "RESULTADOS DEL CORPUS"}</span><strong>{isLoading ? "Consultando..." : (radarMode === "top" ? "Top 5" : `${resultTotal} coincidencia${resultTotal === 1 ? "" : "s"}`)}</strong></div><button type="button" className="icon-button" title="Actualizar" aria-label="Actualizar agenda" onClick={() => void loadRadar({ query: searchText, selectedTopic: topic, selectedEvidence: evidenceFilter, selectedLanguage: language, expanded: radarMode === "explore" }, true)} disabled={isLoading}><Icon name="refresh" size={17}/></button></div>
            <div className="results-list" aria-live="polite">
              {isLoading && <div className="loading-box"><span className="spinner"/>Buscando señales en el snapshot...</div>}
              {!isLoading && !agenda.length && <div className="empty-radar"><Icon name="search" size={24}/><strong>Sin coincidencias verificables</strong><p>{searchDescription || "Prueba con términos más específicos."}</p><button type="button" onClick={() => { setSearchText(""); setTopic(""); setEvidenceFilter(""); void loadRadar({ selectedLanguage: language }); }}>Volver al Top 5</button></div>}
              {!isLoading && agenda.map((item, index) => {
                const state = item.evidence_package.evidence_state;
                return <button type="button" key={item.case_id} className={`radar-story ${selectedId === item.case_id ? "is-selected" : ""}`} onClick={() => void selectCase(item.case_id)} aria-current={selectedId === item.case_id ? "true" : undefined}>
                  <div className="story-top"><span className="story-number">{String(index + 1).padStart(2, "0")}</span><span className="story-section">{item.evidence_package.topic || "Por clasificar"}</span><span className="story-score">{item.attention.score}<small>/100</small></span></div>
                  <strong>{sourceHeadline(item)}</strong>
                  <div className="story-meta"><span>{item.case_languages?.length && (item.case_languages.length > 1 || (item.case_languages[0] !== "es" && item.case_languages[0] !== "spa")) ? `Idiomas: ${item.case_languages.join(", ")} · ` : ""}{item.news_count} noticia{item.news_count !== 1 ? "s" : ""}</span><i/> <span className={stateTone(state) === "green" ? "positive-text" : "caution-text"}>{state.includes("suficiente") ? "Lista para borrador" : state}</span></div>
                  <span className="story-case">{item.case_id} <Icon name="arrow" size={13}/></span>
                </button>;
              })}
            </div>
            <div className="radar-footnote"><Icon name="shield" size={16}/><p>GDELT incluye medios internacionales. El filtro afecta qué eventos se descubren; las fuentes originales de cada expediente permanecen intactas y pueden estar en otros idiomas.</p></div>
          </aside>

          <section id="evidencia" className="investigation-column" aria-label="Cuaderno de investigación">
            <div className="column-caption"><span>02</span><p>CUADERNO DE EVIDENCIA</p><Icon name="file" size={16}/></div>
            {isCaseLoading && <div className="panel-loading"><span className="spinner"/>Abriendo expediente editorial...</div>}
            {!isCaseLoading && !current && <div className="no-case"><Icon name="layers" size={34}/><h2>Empieza por una señal.</h2><p>Selecciona una noticia del radar o haz una búsqueda para abrir su expediente.</p></div>}
            {!isCaseLoading && current && <>
              <div className="investigation-hero">
                <div className="case-eyebrow"><span>EXPEDIENTE / {current.case_id}</span><Marker tone={stateTone(pkg?.evidence_state || "")}>{pkg?.evidence_state || "Sin evidencia"}</Marker></div>
                <h2>{sourceHeadline(selectedFromRadar || current)}</h2>
                <div className="hero-meta"><span>{pkg?.topic || "Sin tema"}</span><i/> <span>{selectedFromRadar?.source || newsEvidence[0]?.source_name || "Fuente del corpus"}</span><i/><span>{selectedFromRadar?.date_origin === "detección" ? "Detectado: " : selectedFromRadar?.date_origin === "publicación" ? "Publicado: " : "Fecha: "}{humanDate(selectedFromRadar?.date)}</span></div>
              </div>
              {selectedFromRadar?.case_languages && selectedFromRadar.case_languages.some(lang => !["es", "spa", "es-es", "es-pa"].includes(lang)) && <div className="language-notice"><Icon name="layers" size={16}/> Este expediente conserva materiales originalmente publicados en: <strong>{selectedFromRadar.case_languages.join(", ")}</strong>. Una traducción no se ha verificado.</div>}
              <div className="report-lede"><span>LECTURA EDITORIAL</span><p>Esta ficha reúne <strong>{newsEvidence.length} referencia{newsEvidence.length !== 1 ? "s" : ""} periodística{newsEvidence.length !== 1 ? "s" : ""}</strong> y <strong>{officialEvidence.length} indicador{officialEvidence.length !== 1 ? "es" : ""} oficial{officialEvidence.length !== 1 ? "es" : ""}</strong> en torno al evento. Solo refleja lo disponible en el corpus: <strong>no certifica la veracidad del titular.</strong></p></div>
              <div className="investigation-block">
                <div className="block-heading"><div><span className="section-index">A /</span><h3>¿Qué sabemos?</h3></div><span className="block-meta">{newsEvidence.length} titular{newsEvidence.length !== 1 ? "es" : ""}</span></div>
                {newsEvidence.length ? <div className="sources-stack">{newsEvidence.map((e, ix) => <button type="button" key={e.evidence_id} className={`source-record ${focusedEvidence === e.evidence_id ? "source-active" : ""}`} onClick={() => setFocusedEvidence(e.evidence_id)}><div className="source-record-head"><span>FUENTE {String(ix + 1).padStart(2, "0")} · {e.source_name}</span><span className="evidence-code">{e.evidence_id}</span></div><strong>{e.value}</strong><p>{e.scope_note || "Alcance no indicado"}</p><span className="source-record-cta">Seleccionar evidencia <Icon name="arrow" size={13}/></span></button>)}</div> : <p className="empty-inline">No hay titulares verificables en este expediente.</p>}
                <div className="caveat-note"><Icon name="alert" size={17}/><p>El conteo de medios o procedencias detectadas ({pkg?.independent_provenances ?? 0}) no verifica independencia editorial. Varias publicaciones pueden replicar una misma fuente original.</p></div>
              </div>
              <div className="investigation-block">
                <div className="block-heading"><div><span className="section-index">B /</span><h3>Contexto, no prueba.</h3></div><span className="block-meta">Indicadores oficiales</span></div>
                {officialEvidence.length ? <div className="indicator-grid">{officialEvidence.map(e => <button type="button" key={e.evidence_id} className={`indicator-card ${focusedEvidence === e.evidence_id ? "source-active" : ""}`} onClick={() => setFocusedEvidence(e.evidence_id)}><span>{e.source_name}</span><strong>{e.value} <small>{e.unit || ""}</small></strong><span className="indicator-period">{e.field} · {e.period || "Sin periodo"}</span><p>{e.scope_note}</p><span className="source-record-cta">Ver trazabilidad <Icon name="arrow" size={13}/></span></button>)}</div> : <div className="empty-inline">No se fuerza un indicador si no se identifica contexto oficial pertinente.</div>}
              </div>
              <div className="investigation-block pending-block">
                <div className="block-heading"><div><span className="section-index">C /</span><h3>Lo que falta verificar.</h3></div><span className="block-meta">Antes del borrador</span></div>
                {pkg?.missing_information?.length ? <ul className="pending-list">{pkg.missing_information.map((x, i) => <li key={i}><span>{String(i + 1).padStart(2, "0")}</span>{x}</li>)}</ul> : <div className="empty-inline">No hay faltantes registrados automáticamente. El editor conserva la responsabilidad de verificar.</div>}
                {!!pkg?.contradictions?.length && <div className="conflict-panel"><strong><Icon name="alert" size={17}/> Señales potencialmente contradictorias</strong>{pkg.contradictions.map((c, i) => <p key={i}>{c}</p>)}<small>Detección automática indicativa; no determina qué versión es correcta.</small></div>}
              </div>
              <details className="methodology"><summary><span><Icon name="layers" size={17}/> Por qué importa para la agenda</span><span className="method-score">{current.attention.score}/100 <Icon name="chevron" size={15}/></span></summary><p className="formula-note">{current.attention.formula} · {current.attention.rules_version}. Reglas heurísticas propuestas, no medidas de verdad, impacto probado o audiencia.</p>{(["R","I","U","N","E"] as const).map(key => <div className="rule-measure" key={key}><div><strong>{key}</strong><div><span style={{ width: `${Math.max(0, Math.min(1, current.attention.components[key] ?? 0)) * 100}%` }}/></div><span>{Math.round((current.attention.components[key] ?? 0) * 100)}%</span></div><p>{current.attention.explanations[key]}</p></div>)}</details>
            </>}
          </section>

          <aside id="decision" className="decision-column" aria-label="Mesa de decisión editorial">
            <div className="column-caption"><span>03</span><p>DECISIÓN EDITORIAL</p><Icon name="shield" size={16}/></div>
            {!current ? <div className="decision-empty">Selecciona un caso para habilitar las acciones de revisión.</div> : <>
              <div className="decision-status"><span className="tiny-label">ESTADO ACTUAL</span><h2>{current.workflow.state}</h2><p>{current.workflow.recommended_action}</p><div className="status-line"><span className="status-led"/><strong>No autorizado para publicar</strong></div></div>
              <div className="decision-section evidence-focus"><div className="decision-section-title"><span>EVIDENCIA EN FOCO</span><Icon name="file" size={16}/></div>{focused ? <><strong>{focused.source_name}</strong><p>{focused.value}</p><div className="focus-code">{focused.evidence_id} · campo: {focused.field}</div><div className="evidence-focus-actions"><button onClick={() => void copyText(`${focused.evidence_id} | ${focused.field} | ${focused.value} | ${focused.url || ""}`)}><Icon name="copy" size={15}/> Copiar referencia</button>{focused.url && <a href={focused.url} target="_blank" rel="noopener noreferrer">Fuente <Icon name="external" size={14}/></a>}</div></> : <p className="focus-placeholder">Selecciona un titular o indicador del cuaderno para inspeccionar su ID y campo de procedencia.</p>}</div>
              <div className="decision-section generate-area"><div className="decision-section-title"><span>BORRADOR ASISTIDO</span><Icon name="spark" size={17}/></div><div className="draft-tabs" role="tablist" aria-label="Formato editorial">{(["brief","script","digital"] as DraftMode[]).map(m => <button type="button" role="tab" aria-selected={mode === m} className={mode === m ? "tab-active" : ""} onClick={() => setMode(m)} key={m}>{m === "brief" ? "Brief" : m === "script" ? "Guion" : "Digital"}</button>)}</div><div className="format-caption">{mode === "brief" ? "≤250 palabras · enfoque, fuentes y 3 preguntas" : mode === "script" ? "Guion estimado de 45–60 segundos" : "Copy digital de máximo 80 palabras"}</div><button type="button" className="generate-button" onClick={() => void generateDraft()} disabled={!detail?.workflow.draft_enabled || isGenerating}><Icon name={detail?.workflow.draft_enabled ? "spark" : "lock"} size={17}/>{isGenerating ? "Preparando borrador..." : "Preparar borrador"}<Icon name="arrow" size={16}/></button>{!detail?.workflow.draft_enabled && <p className="disabled-explanation">Bloqueado: este caso requiere evidencia adicional.</p>}{selectedDraft && <div className="draft-result"><div className="draft-result-head"><Marker tone="green">{selectedDraft.cached ? "Cache validado" : "Generado"}</Marker><span>{selectedDraft.model}</span></div><div className="draft-text">{selectedDraft.text}</div>{selectedDraft.quality && <div className="draft-quality"><span>IDs de citas: {Math.round((selectedDraft.quality.citation_coverage ?? 0) * 100)}% <small>(no acredita sustento semántico)</small></span>{selectedDraft.quality.main_text_word_count != null && <span>Palabras: {selectedDraft.quality.main_text_word_count}</span>}</div>}<button type="button" onClick={() => void copyText(selectedDraft.text)} className="copy-draft"><Icon name="copy" size={14}/> Copiar texto para revisar</button><div className="draft-caveat">Texto asistido: verificar cada afirmación antes de aprobar.</div></div>}</div>
              <div className="decision-section human-review"><div className="decision-section-title"><span>DICTAMEN HUMANO</span><Icon name="check" size={17}/></div><label htmlFor="reviewer" className="review-label">PERSONA REVISORA</label><input id="reviewer" value={reviewer} onChange={e => setReviewer(e.target.value)} placeholder="Nombre o identificador" maxLength={120}/><label htmlFor="review-note" className="review-label">NOTA EDITORIAL</label><textarea id="review-note" value={reviewNote} onChange={e => setReviewNote(e.target.value)} placeholder="Verificaciones o cambios que requiere el tema..." maxLength={2000}/><div className="review-buttons"><button type="button" onClick={() => void submitReview("approve")} disabled={!canApprove || isReviewing} className="approve-btn"><Icon name="check" size={16}/> Aprobar borrador</button><button type="button" onClick={() => void submitReview("correct")} disabled={!reviewer.trim() || isReviewing} className="correct-btn">Pedir corrección</button><button type="button" onClick={() => void submitReview("discard")} disabled={!reviewer.trim() || isReviewing} className="discard-btn">Descartar</button></div>{current.workflow.human_review && <div className="review-record"><span>ÚLTIMO REGISTRO</span><strong>{current.workflow.human_review.state}</strong><small>{current.workflow.human_review.reviewer} · {humanDate(current.workflow.human_review.updated_at)}</small>{current.workflow.human_review.note && <p>{current.workflow.human_review.note}</p>}</div>}<p className="review-disclaimer">La aprobación registra una decisión de borrador, nunca una publicación. La interfaz requiere haber cargado un borrador antes de permitir aprobar.</p></div>
            </>}
          </aside>
        </div>
        <footer className="page-footer"><span>TVN MEDIA COPILOT · MESA DE REDACCIÓN</span><span>Fuentes públicas · Investigación asistida · Revisión obligatoria</span><span>Los titulares no constituyen verificación independiente.</span></footer>
      </main>
    </div>
  );
}
