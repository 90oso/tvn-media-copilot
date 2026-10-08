from dataclasses import dataclass
import pandas as pd
from app.schemas.evidence import EvidencePackage

@dataclass(frozen=True)
class AttentionComponents:
    relevance:float; impact:float; urgency:float; novelty:float; evidence:float
    def validate(self):
        for k,v in self.__dict__.items():
            if not 0<=v<=1: raise ValueError(f'{k} debe estar entre 0 y 1')
    @property
    def total(self):
        self.validate(); return round(30*self.relevance+25*self.impact+20*self.urgency+15*self.novelty+10*self.evidence,2)
    @property
    def band(self):
        p=self.total
        return 'bajo' if p<40 else ('medio' if p<70 else 'alto')

def _panama(news):
    t=' '.join(str(x) for c in ('titulo','medio','origen') if c in news.columns for x in news[c].dropna()).lower()
    return any(x in t for x in ('panamá','panama','canal'))
def _urgency(news, snapshot_reference=None):
    if news.empty:return .3
    pub = (
        pd.to_datetime(news['fecha_publicacion'],errors='coerce',utc=True)
        if 'fecha_publicacion' in news.columns else pd.Series(pd.NaT,index=news.index)
    )
    det = (
        pd.to_datetime(news['fecha_deteccion'],errors='coerce',utc=True)
        if 'fecha_deteccion' in news.columns else pd.Series(pd.NaT,index=news.index)
    )
    # La detección es solo fallback operativo de recencia; nunca se reescribe como publicación.
    d=pub.fillna(det).dropna()
    if d.empty:return .3
    newest=d.max()
    ref=pd.Timestamp(snapshot_reference) if snapshot_reference is not None else newest
    if ref.tzinfo is None: ref=ref.tz_localize('UTC')
    age=max(0.0,(ref-newest).total_seconds()/86400)
    return 1.0 if age<=1 else (.8 if age<=3 else (.6 if age<=7 else (.4 if age<=14 else (.2 if age<=30 else .1))))

def _novelty(news):
    n=len(news)
    return 1.0 if n<=1 else (.8 if n==2 else (.65 if n==3 else (.5 if n<=5 else .35)))

def propose_components(news:pd.DataFrame,pkg:EvidencePackage,snapshot_reference=None)->AttentionComponents:
    # PROPUESTA versionada: el documento define qué mide cada componente, no estas reglas.
    r=1.0 if _panama(news) else .6
    official=sum(1 for e in pkg.evidence if e.source_type=='official_indicator')
    prov=pkg.independent_provenances
    i=.8 if official and prov>=2 else (.6 if official or prov>=2 else .35)
    u=_urgency(news,snapshot_reference); n=_novelty(news)
    e=.9 if prov>=3 else (.7 if prov==2 else (.4 if prov==1 else .1))
    if official:e=min(1.0,e+.1)
    return AttentionComponents(round(r,2),round(i,2),round(u,2),round(n,2),round(e,2))


def explain_components(news:pd.DataFrame,pkg:EvidencePackage,components:AttentionComponents)->dict:
    official=sum(1 for e in pkg.evidence if e.source_type=='official_indicator')
    return {
        'R':f'Relevancia Panamá/temática: {components.relevance:.2f}.',
        'I':f'Impacto potencial conservador: {components.impact:.2f}; contexto oficial={official}, procedencias={pkg.independent_provenances}.',
        'U':f'Urgencia por recencia frente al corte del snapshot: {components.urgency:.2f}.',
        'N':f'Novedad según tamaño del cluster ({len(news)} registros), sin premiar duplicación: {components.novelty:.2f}.',
        'E':f'Evidencia según procedencias independientes y contexto oficial: {components.evidence:.2f}.',
    }
