"use client";

import { useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AgendaItem = any;

type Generated = any;

function Pill({ children, tone = "neutral" }: { children: React.ReactNode; tone?: string }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}

function ScoreBar({ label, value, text }: { label: string; value: number; text?: string }) {
  return (
    <div className="score-row">
      <div className="score-top"><strong>{label}</strong><span>{Math.round(value * 100)}%</span></div>
      <div className="score-track"><span style={{ width: `${Math.round(value * 100)}%` }} /></div>
      {text && <p>{text}</p>}
    </div>
  );
}

export default function Home() {
  const [agenda, setAgenda] = useState<AgendaItem[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [selected, setSelected] = useState<AgendaItem | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [generated, setGenerated] = useState<Generated | null>(null);
  const [generateLoading, setGenerateLoading] = useState(false);
  const [mode, setMode] = useState<"brief" | "script" | "digital">("brief");
  const [reviewNote, setReviewNote] = useState("");
  const [reviewMsg, setReviewMsg] = useState("");
  const [error, setError] = useState("");

  async function refreshAgenda() {
    setLoading(true);
    setError("");
    try {
      const [h, a] = await Promise.all([
        fetch(`${API}/health`, { cache: "no-store" }).then(r => r.ok ? r.json() : null),
        fetch(`${API}/agenda?limit=5`, { cache: "no-store" }).then(r => {
          if (!r.ok) throw new Error("No fue posible cargar la agenda");
          return r.json();
        }),
      ]);
      setHealth(h);
      setAgenda(a.items || []);
      if (!selected && a.items?.length) selectCase(a.items[0]);
    } catch (e: any) {
      setError(e.message || "No fue posible conectar con la API");
    } finally {
      setLoading(false);
    }
  }

  async function selectCase(item: AgendaItem) {
    setSelected(item);
    setGenerated(null);
    setReviewMsg("");
    setDetailLoading(true);
    try {
      const r = await fetch(`${API}/topics/${item.case_id}/analysis`, { cache: "no-store" });
      if (!r.ok) throw new Error("No fue posible cargar el caso");
      setDetail(await r.json());
    } catch (e: any) {
      setError(e.message || "Error cargando el caso");
    } finally {
      setDetailLoading(false);
    }
  }

  async function generateDraft() {
    if (!detail) return;
    setGenerateLoading(true);
    setGenerated(null);
    setError("");
    try {
      const r = await fetch(`${API}/generate/${detail.case_id}?mode=${mode}`, { method: "POST" });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(body?.detail?.message || body?.detail?.provider_detail || body?.detail || "No fue posible generar el borrador");
      setGenerated(body);
    } catch (e: any) {
      setError(e.message || "Error de generación");
    } finally {
      setGenerateLoading(false);
    }
  }

  async function review(action: "approve" | "correct" | "discard") {
    if (!detail) return;
    setReviewMsg("");
    setError("");
    try {
      const r = await fetch(`${API}/reviews/${detail.case_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, reviewer: "editor", note: reviewNote }),
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(body?.detail?.message || body?.detail || "No fue posible guardar la revisión");
      setReviewMsg(`Estado guardado: ${body.review.state}`);
      setReviewNote("");
      await selectCase(selected!);
      await refreshAgenda();
    } catch (e: any) {
      setError(e.message || "Error guardando revisión");
    }
  }

  useEffect(() => { refreshAgenda(); }, []);

  const pkg = detail?.evidence_package;
  const att = detail?.attention;
  const workflow = detail?.workflow;
  const newsEvidence = useMemo(() => (pkg?.evidence || []).filter((e: any) => e.source_type === "news"), [pkg]);
  const officialEvidence = useMemo(() => (pkg?.evidence || []).filter((e: any) => e.source_type === "official_indicator"), [pkg]);

  return (
    <main>
      <header className="hero">
        <div>
          <div className="kicker">TVN Media · Copiloto editorial</div>
          <h1>De la señal a la decisión</h1>
          <p className="subtitle">Agenda priorizada, evidencia trazable y borradores responsables. La prioridad nunca equivale a publicación automática.</p>
        </div>
        <div className="hero-status">
          <Pill tone={health ? "ok" : "warn"}>{health ? `API ${health.version}` : "API sin conexión"}</Pill>
          <span>Top 5 editorial</span>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {reviewMsg && <div className="alert alert-ok">{reviewMsg}</div>}

      <section className="summary-grid">
        <article className="metric-card"><span>Casos priorizados</span><strong>{agenda.length}</strong><small>Ranking R/I/U/N/E</small></article>
        <article className="metric-card"><span>Con borrador habilitado</span><strong>{agenda.filter(x => x.workflow?.draft_enabled).length}</strong><small>Según suficiencia de evidencia</small></article>
        <article className="metric-card"><span>Revisión humana</span><strong>Obligatoria</strong><small>Nunca se publica automáticamente</small></article>
      </section>

      <section className="workspace">
        <aside className="agenda-panel">
          <div className="panel-head"><div><div className="kicker">Agenda</div><h2>Top 5</h2></div><button className="ghost" onClick={refreshAgenda}>Actualizar</button></div>
          {loading ? <div className="empty">Cargando agenda…</div> : agenda.map((item, index) => (
            <button key={item.case_id} className={`agenda-item ${selected?.case_id === item.case_id ? "active" : ""}`} onClick={() => selectCase(item)}>
              <div className="agenda-rank">#{index + 1}</div>
              <div className="agenda-copy">
                <div className="agenda-line"><strong>{item.attention.score}/100</strong><Pill tone={item.attention.band === "alto" ? "high" : "neutral"}>{item.attention.band}</Pill></div>
                <span className="case-id">{item.case_id}</span>
                <small>{item.news_count} noticia{item.news_count === 1 ? "" : "s"} · {item.evidence_package.evidence_state}</small>
              </div>
            </button>
          ))}
        </aside>

        <section className="detail-panel">
          {!detail || detailLoading ? <div className="empty large">Selecciona un caso para revisar la evidencia.</div> : <>
            <div className="case-header">
              <div>
                <div className="kicker">Caso editorial</div>
                <h2>{detail.case_id}</h2>
                <div className="pill-row">
                  <Pill tone="high">{att.score}/100 · {att.band}</Pill>
                  <Pill tone={pkg.evidence_state.includes("suficiente") ? "ok" : "warn"}>{pkg.evidence_state}</Pill>
                  <Pill>{pkg.topic || "sin tema"}</Pill>
                  <Pill>{workflow.state}</Pill>
                </div>
              </div>
              <div className="score-big"><strong>{att.score}</strong><span>/100</span></div>
            </div>

            <div className="tabs-grid">
              <section className="inner-card">
                <div className="section-title"><h3>Por qué está priorizado</h3><span>{att.formula}</span></div>
                {Object.entries(att.components).map(([key, value]: any) => <ScoreBar key={key} label={key} value={value} text={att.explanations[key]} />)}
              </section>

              <section className="inner-card">
                <div className="section-title"><h3>Estado editorial</h3><span>Human-in-the-loop</span></div>
                <p className="workflow-state">{workflow.state}</p>
                <p>{workflow.recommended_action}</p>
                <div className="rule-box"><strong>Publicación automática: NO</strong><span>El sistema solo prepara señales y borradores revisables.</span></div>
                {workflow.human_review && <div className="review-history"><strong>Última revisión</strong><span>{workflow.human_review.reviewer} · {workflow.human_review.updated_at}</span>{workflow.human_review.note && <p>{workflow.human_review.note}</p>}</div>}
              </section>
            </div>

            <section className="inner-card full">
              <div className="section-title"><h3>Paquete de evidencia</h3><span>{pkg.independent_provenances} procedencia(s) independiente(s)</span></div>
              <div className="evidence-grid">
                <div>
                  <h4>Noticias</h4>
                  {newsEvidence.map((e: any) => <article className="evidence-item" key={e.evidence_id}><span className="evidence-id">{e.evidence_id}</span><strong>{e.value}</strong><small>{e.source_name}{e.period ? ` · ${e.period}` : ""}</small><p>{e.scope_note}</p>{e.url && <a href={e.url} target="_blank" rel="noreferrer">Abrir fuente ↗</a>}</article>)}
                </div>
                <div>
                  <h4>Contexto oficial</h4>
                  {officialEvidence.length ? officialEvidence.map((e: any) => <article className="evidence-item official" key={e.evidence_id}><span className="evidence-id">{e.evidence_id}</span><strong>{e.field}: {e.value} {e.unit || ""}</strong><small>{e.source_name} · {e.period}</small><p>{e.scope_note}</p></article>) : <p className="muted">No se fuerza contexto oficial cuando no es pertinente.</p>}
                  {!!pkg.missing_information?.length && <div className="warning-box"><strong>Faltantes</strong>{pkg.missing_information.map((x: string) => <p key={x}>• {x}</p>)}</div>}
                </div>
              </div>
              {!!pkg.contradictions?.length && <div className="contradiction-box"><strong>Contradicciones potenciales</strong>{pkg.contradictions.map((x: string) => <p key={x}>{x}</p>)}</div>}
            </section>

            <section className="inner-card full">
              <div className="section-title"><h3>Generación editorial</h3><span>Gemini · solo con evidencia suficiente</span></div>
              <div className="mode-row">
                {(["brief", "script", "digital"] as const).map(m => <button key={m} className={`mode-btn ${mode === m ? "active" : ""}`} onClick={() => setMode(m)}>{m === "brief" ? "Brief" : m === "script" ? "Guion 45–60 s" : "Copy digital"}</button>)}
                <button className="primary" disabled={!workflow.draft_enabled || generateLoading} onClick={generateDraft}>{generateLoading ? "Generando…" : "Generar borrador"}</button>
              </div>
              {!workflow.draft_enabled && <p className="muted">Este caso requiere más evidencia antes de generar un borrador.</p>}
              {generated && <div className="draft-box"><div className="draft-meta"><Pill tone="ok">{generated.cached ? "cache validado" : "generado"}</Pill><span>{generated.model} · {generated.attempts} intento(s)</span></div><pre>{generated.text}</pre>{generated.quality && <div className="quality-row"><span>Cobertura de citas: {Math.round((generated.quality.citation_coverage || 0) * 100)}%</span><span>Palabras: {generated.quality.main_text_word_count ?? "—"}</span>{generated.quality.estimated_duration_seconds && <span>Duración estimada: {generated.quality.estimated_duration_seconds}s</span>}</div>}</div>}
            </section>

            <section className="inner-card full review-card">
              <div className="section-title"><h3>Revisión humana</h3><span>Decisión editorial</span></div>
              <textarea value={reviewNote} onChange={e => setReviewNote(e.target.value)} placeholder="Nota de corrección o comentario editorial…" />
              <div className="review-actions">
                <button className="approve" disabled={!workflow.draft_enabled} onClick={() => review("approve")}>Aprobar como borrador</button>
                <button className="correct" onClick={() => review("correct")}>Solicitar corrección</button>
                <button className="discard" onClick={() => review("discard")}>Descartar</button>
              </div>
            </section>
          </>}
        </section>
      </section>
    </main>
  );
}
