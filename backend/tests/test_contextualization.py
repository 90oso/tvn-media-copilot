import pandas as pd
from app.services.contextualization import contextualize_topic

def test_economy_context():
    df=pd.DataFrame([{'indicador_id':'FP.CPI.TOTL.ZG','anio':'2024','valor':'1.5','unidad':'porcentaje','fuente_url':'https://example.org','licencia':'CC BY 4.0'}])
    c,n=contextualize_topic('economía',df); assert len(c)==1; assert 'No prueba causalidad' in c[0]['scope_note']
def test_no_forced_natural_event_context():
    c,n=contextualize_topic('eventos naturales',pd.DataFrame()); assert c==[]; assert n
