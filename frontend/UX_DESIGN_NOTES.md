# UX / Mesa de Redacción

Tres superficies permanentes: **Radar** (descubrimiento), **Cuaderno** (evidencia y vacíos) y **Decisión** (borradores y revisión).

- El evento se identifica visualmente por su **titular**, no por su ID hash; el ID sigue disponible para auditoría.
- El score es secundario y su metodología se despliega a demanda.
- El modelo nunca se presenta como verificador de veracidad.
- El número de procedencias se acompaña de una advertencia: contar medios no certifica corroboración independiente.
- El editor puede consultar documentos de procedencia y copiar evidencia por ID/campo.
- Colores: papel y tinta para un lenguaje editorial; rojo reservado a identidad/decisiones, ámbar para incertidumbre y verde para suficiencia.
- Tipografías locales y SVG inline: **sin dependencias externas de diseño ni assets ocultos**. Modo oscuro/claro mediante variable de tema.
- El diseño responde a escritorio, tablet y móvil con un flujo apilado.

La implementación usa los contratos JSON de FastAPI existentes y añade solo `GET /explore`; no sustituye ranking, revisión ni generación por datos simulados.
