# Asistente de IA para Diversidad, Equidad e Inclusión
Documentación técnica · Arquitectura · Preparación de datos · Despliegue

⚠️ Autoría

Este proyecto y su documentación fueron desarrollados por
la AFD – Agence Française de Développement
y se publican como open-source para uso, adaptación y desarrollo por parte de la comunidad.

“Tecnología abierta al servicio de la equidad y la inclusión.”


## Asistente de IA para DEI (RAG con Thinkstack + WordPress)

DALIA es un asistente conversacional especializado en Diversidad, Equidad e Inclusión (DEI) diseñado para empresas colombianas.  
Este documento describe **cómo replicar una IA con enfoque DEI**, desde la preparación de la información (curaduría, parsing, limpieza de datos) hasta la integración final en WordPress mediante iframe.

---

## 1. Arquitectura General del Sistema

La IA con enfoque DEI se construye únicamente con:

Datos (CSV + PDFs DEI + normativa)
↓
Curaduría y Parsing (LlamaParse, limpieza, normalización)
↓
Thinkstack AI (RAG + base documental + diseño del asistente)
↓
Código de integración <iframe>
↓
WordPress (interfaz visible al usuario)

## 2. Requisitos Previos

### 2.1. Cuentas
- Thinkstack AI (para chatbot y RAG).
- WordPress (para publicar el chatbot).

### 2.2. Insumos necesarios
- **Documentos de DEI** del cliente:
  - Manuales internos.
  - Políticas de inclusión.
  - Programas de bienestar.
  - Guías de selección y reclutamiento.
- **Normativa colombiana**:
  - Leyes mas actualizadas.
  - Resoluciones del Ministerio de Trabajo.
  - Documentos oficiales sobre no discriminación laboral.
- **Bases de datos CSV**:
  - Estructura de personal.
  - Salarios.
  - Antigüedad.
  - Encuestas internas.

---

## 3. Curaduría Documental (Documentos DEI + Normativa)

Antes de subir información a Thinkstack es crítico hacer **curaduría** para evitar ruido en el modelo.

### 3.1. Selección de documentos
Elegir únicamente archivos que incluyan:

- Información oficial y vigente.
- Políticas aplicables a procesos de inclusión laboral.
- Normativa colombiana relacionada con:
  - Igualdad salarial.
  - Acceso al empleo.
  - Accesibilidad.
  - Medidas antidiscriminación.

Documentos no relevantes (presentaciones, material comercial, duplicados) deben **excluirse**.

---

## 4. Parsing profesional de PDFs (LlamaParse)

Muchos documentos vienen con:

- Diagramas
- Flujos de procesos
- Imágenes insertadas
- Tablas no estructuradas
- Elementos visuales que rompen el texto

Para que Thinkstack pueda entenderlos, deben procesarse con una herramienta de Parsing, se recomienda **LlamaParse**.

### 4.1. Objetivo del parsing
- Convertir PDFs complejos en texto estructurado.
- Extraer tablas a formato legible.
- Eliminar ruido visual.
- Mantener jerarquías, títulos y numeración.

### 4.2. Flujo de trabajo recomendado
1. Subir PDF a LlamaParse.
2. Exportar como `.md` o `.txt` estructurado.
3. Revisar manualmente:
   - Coherencia del orden de lectura.
   - Tablas correctamente parseadas.
   - Que no falte información legal.
4. Subir el documento parseado a Thinkstack en lugar del PDF original.

> Esto mejora drásticamente la precisión del RAG.

### 4.3 Flujo de trabajo para un parsing masivo con LLamaParse
Este script permite convertir automáticamente múltiples documentos (PDF, DOCX, PPTX, etc.) de una carpeta a JSON o Markdown usando la API de LlamaParse.

Es la forma recomendada para generar datasets limpios para RAG.

✔️ Requisitos previos

Instalar dependencias:

pip install llama-parse llama-index python-dotenv


Configurar tu API Key:

export LLAMA_CLOUD_API_KEY="TU_API_KEY"


En Windows (PowerShell):

$env:LLAMA_CLOUD_API_KEY="TU_API_KEY"

✔️ ¿Qué hace?

Recibe una carpeta con documentos

Envía cada archivo a LlamaParse

Descarga la versión parseada:

JSON → estructura + metadata + texto

MD → texto plano para ingestion inmediata en RAG

Guarda los resultados en otra carpeta

▶️ Cómo usarlo desde terminal
python batch_llamaparse.py \
  --input_dir ./docs_raw \
  --output_dir ./docs_parsed \
  --format md


Formatos disponibles:

json → ideal para RAG avanzado, extracción de tablas, metadata

md → ideal para ingestion rápida en vector stores

▶️ Cómo integrarlo en un flujo de Python
from batch_llamaparse import batch_parse

batch_parse(
    input_dir="docs_raw",
    output_dir="docs_parsed",
    output_format="md"
)

## 5. Preparación de Bases de Datos (CSV)

Thinkstack no admite CSV con columnas irregulares o datos inconsistentes.  
Hay que preparar los archivos antes de subirlos.

### 5.1. Pasos indispensables

#### 1) **Limpieza**
- Eliminar filas vacías.
- Unificar formatos de fecha.
- Convertir salarios a valores numéricos.
- Homologar categorías de cargo.
- Convertir textos tipo "H"/"M"/"hombre"/"mujer" a una sola convención.

#### 2) **Normalización y parametrización**
Todas las columnas deben tener nombres **estandarizados**, sin carácteres especiales ni espacios (en lugar de espacio usar "_"). Ejemplo:

| Columna            | Descripción breve (≤150 caracteres)                  |
|--------------------|------------------------------------------------------|
| `Sexo`             | Sexo declarado: Hombre o Mujer                       |
| `Nivel_de_Gestion` | Clasificación interna del cargo                      |
| `Salario`          | Salario mensual neto o bruto según dataset           |
| `Antiguedad_dias`  | Tiempo total en la empresa (en días)                 |
| `Edad`             | Edad del colaborador                                 |
| `Ultimo_Cargo_Dias`| Tiempo en el cargo actual                            |

#### 3) **Verificación**
Asegurar:

- Que no hay columnas duplicadas.
- Que todas las filas tienen el mismo número de columnas.
- Que Thinkstack pueda interpretarlas sin error (ver límites abajo).

---
### 5.2) Ejemplo de Pipeline general de limpieza de datos en python usando ej_data_cleaning.py

Este codigo permite realizar una limpieza estandarizada sobre archivos CSV antes de ser usados en análisis o ingestion en un sistema RAG.

✔️ ¿Qué hace?

Carga el CSV

Estandariza nombres de columnas

Elimina columnas 100% nulas

Genera reporte de valores faltantes

Imputa nulos (numéricos y categóricos)

Elimina duplicados

Convierte tipos de datos

Maneja outliers con IQR (capado o eliminación)

Guarda el archivo limpio

▶️ Cómo usarlo desde terminal
python ej_data_cleaning.py \
  --input ruta/dataset.csv \
  --output ruta/dataset_limpio.csv


Parámetros opcionales:

--sep ";"
--encoding "latin-1"

▶️ Cómo usarlo desde otro script de Python
from data_cleaning_template import clean_dataset

df_limpio = clean_dataset(
    path_in="data/raw.csv",
    path_out="data/clean.csv"
)


Esto permite integrarlo fácilmente en pipelines más grandes (ETL, ingestion RAG, etc.).
## 6. Límites y consideraciones de Thinkstack

### 6.1. Tamaños máximos
- Documentos demasiado grandes deben dividirse.
- CSVs muy pesados deben subirse por partes o reducirse.

### 6.2. Tipos de contenido que Thinkstack NO interpreta bien
- PDFs escaneados sin OCR.
- Imágenes de tablas.
- Gráficos de flujo incrustados.

(De ahí la importancia del **parsing** previo.)

### 6.3. RAG mínimo
Mientras más limpio y estructurado esté el dataset:

- Mejor responde la IA.
- Menos alucina.
- Más consistente es el análisis.

---

## 7. Configuración del Chatbot en Thinkstack

### 7.1. Prompt del sistema (evitar sesgos)

Se recomienda incluir:

- Tono neutral, profesional e incluyente.
- Evitar lenguaje discriminatorio.
- Evitar sesgos de género en ejemplos.
- Priorizar normativa colombiana.

El prompt del agente que se ha usado en Dalia se divide en:

#### 1) **agent_persona**:
  descripcion: >
    Experta en Diversidades humanas, Equidad de género e Inclusión laboral y
    comunitaria en Colombia, con experiencia en políticas públicas, inclusión
    y enfoque de género, diferencial e interseccional. Ofrece respuestas claras,
    prácticas y fundamentadas, priorizando la utilidad y la acción.
  principios_de_uso:
    - Usa marcos de la OIT, ONU, OCDE y leyes colombianas solo cuando se solicite
      o sea estrictamente indispensable.
    - Mantiene enfoque de derechos humanos y no discriminación.
    - Se apega siempre al contexto colombiano.
  objetivo: >
    Garantizar que la IA responda de forma técnica, contextualizada, libre de sesgos
    y basada en la información suministrada por los documentos y datasets cargados.

#### 2) **guidelines_respuestas**:
  objetivo_general: >
    Ofrecer orientación y análisis especializado en DEI en el contexto colombiano,
    combinando rigor técnico con lenguaje incluyente, claro, accesible y respetuoso.
    Responder siempre en español, basándose en derechos humanos y en la evidencia
    académica disponible.

  formato_obligatorio:
    - Idea central – breve resumen introductorio del tema.
    - Desarrollo – argumentos, explicaciones, ejemplos o casos relevantes.
    - Referencia normativa o fuente (solo si se solicita explícitamente) – citar leyes,
      políticas o documentos recientes.
    - Conclusión o recomendación final.

  tono:
    - Amable, respetuoso, profesional y empático.
    - Culturalmente sensible al contexto colombiano.
    - Reconoce diversidad étnica, cultural, social, de género y capacidad.
    - Aplica enfoque interseccional.
    - Evita neutralidad que normalice discriminación.
    - Formula preguntas solo cuando es imprescindible y justifica la necesidad.

  estructura_y_claridad:
    - Comenzar siempre con una idea central clara.
    - Usar párrafos separados y coherentes.
    - Evitar tecnicismos innecesarios o explicarlos cuando se utilicen.
    - Adaptar lenguaje para públicos diversos (RH, líderes, equipos comunitarios).

  contextualizacion:
    - Referenciar leyes y políticas públicas de Colombia cuando sea pertinente.
    - Reconocer la existencia de grupos poblacionales protegidos.
    - Sugerir anonimización en caso de recibir o analizar datos sensibles.

  fuentes_y_transparencia:
    - Consultar siempre la base documental y datasets internos cargados en Thinkstack.
    - Citar documentos por nombre, institución, autor y año si la referencia se solicita.
    - Priorizar artículos revisados por pares, informes técnicos, organismos multilaterales
      y centros de investigación reconocidos.
    - Indicar si el acceso a la información fue limitado.
    - Marcar traducciones automáticas cuando aplique.

  lenguaje_inclusivo:
    - Usar expresiones inclusivas como “personas con discapacidad”, “personas LGBTIQ+”.
    - Evitar masculino genérico y estereotipos por género, edad, origen étnico,
      discapacidad u otra condición.
    - Evitar metáforas o ejemplos que impliquen jerarquías de género.

  reconocimiento_de_limites:
    - En temas controvertidos, presentar varias perspectivas sin tomar partido.
    - Si no existe evidencia suficiente, indicarlo explícitamente.
    - Evitar información no verificada o especulativa.
    - En temas legales o médicos, ofrecer orientación general y sugerir consulta profesional.
    - Prevenir alucinaciones del modelo mediante precisión en el contenido.

---

## 8. Integración con WordPress

wordpress_integracion:
  descripcion_general: >
    Antes de insertar el iframe del chatbot generado por Thinkstack, es necesario
    preparar el entorno de WordPress para asegurar compatibilidad, seguridad y
    correcta visualización del asistente IA con enfoque DEI. Esta sección describe los pasos
    previos, la integración del código y la verificación final.

  pasos_previos_en_wordpress:
    verificar_roles_permisos:
      descripcion: >
        Asegurarse de tener permisos de administrador o editor con capacidad
        para crear páginas, insertar código HTML y usar plugins como Code Snippets
        o constructores visuales. Sin estos permisos, la integración no podrá completarse.
      acciones:
        - Confirmar rol de usuario actual en WordPress.
        - Verificar que la instalación permite contenido embebido (iframes).

    revisar_tema_y_constructor:
      descripcion: >
        Revisar si el sitio usa un constructor (Elementor, Divi, Gutenberg) para
        determinar dónde se insertará el iframe. Algunos temas limitan HTML directo
        o requieren módulos específicos para contenido embebido.
      recomendaciones:
        - Si se usa Elementor → habilitar el widget HTML.
        - Si se usa Gutenberg → habilitar bloque HTML personalizado.
        - Si el tema restringe iframes → usar Code Snippets como alternativa.

    habilitar_https:
      descripcion: >
        El iframe de Thinkstack funciona correctamente solo si el sitio WordPress
        está configurado en HTTPS. De lo contrario, el navegador bloqueará el contenido.
      acciones:
        - Verificar que el dominio esté en https://
        - Activar plugin “Really Simple SSL” si es necesario.

    crear_pagina_contenedor:
      descripcion: >
        Antes de incrustar el chatbot, se recomienda crear una página dedicada
        que actuará como contenedor principal del asistente DALIA.
      pasos:
        - Ir al Panel → Páginas → “Añadir nueva”.
        - Asignar título sugerido: “Asistente DEI”.
        - Publicar la página aun sin contenido.
      notas:
        - Evitar plantillas con barras laterales o restricciones de ancho.
        - Preferir plantilla “Full Width” o “Canvas”.

  integracion_iframe:
    obtener_iframe_desde_thinkstack: >
      Desde la sección “Embed / Inline” en Thinkstack AI, copiar el iframe
      correspondiente al agente IA creado en thinkstack. Debería de verse algo así:
      <iframe src="https://app.thinkstack.ai/bot/index.html?chatbot_id=xxxx&type=inline"
      frameborder="0" width="100%" height="100%" style="min-height: 500px;"></iframe>

    metodos_de_insercion:
      metodo_1_bloque_html:
        descripcion: >
          Ideal para sitios con Gutenberg o constructores modernos. Consiste en
          pegar el iframe directamente en la página creada previamente.
        pasos:
          - Editar la página contenedora.
          - Insertar bloque “HTML personalizado”.
          - Pegar el iframe proporcionado por Thinkstack.
          - Actualizar y visualizar.

      metodo_2_elementor:
        descripcion: >
          Utilizar el widget “HTML” de Elementor para incrustar el iframe con total
          control sobre estilos, márgenes y estructura visual.
        pasos:
          - Abrir la página en Elementor.
          - Arrastrar el widget “HTML”.
          - Pegar el iframe.
          - Ajustar altura mínima o padding.

      metodo_3_code_snippets_con_shortcode:
        descripcion: >
          Recomendado cuando el tema bloquea iframes o se requiere reutilizar el
          chatbot en varias páginas. Se crea un shortcode que devuelve el iframe.
        snippet_php: |
          function dalia_chatbot() {
              return '<iframe
                  src="https://app.thinkstack.ai/bot/index.html?chatbot_id=xxxx&type=inline"
                  frameborder="0"
                  width="100%"
                  height="100%"
                  style="min-height: 500px;"></iframe>';
          }
        uso:
          - Insertar en cualquier página con: [dalia]

  verificacion_final:
    pruebas_recomendadas:
      - Probar carga del chatbot desde un navegador en incógnito.
      - Confirmar que no existan errores de contenido mixto HTTP/HTTPS.
      - Realizar una pregunta simple y verificar respuesta desde Thinkstack.
      - Validar que el iframe responde bien en dispositivos móviles.

    posibles_errores_y_soluciones:
      error_iframe_bloqueado: >
        Los navegadores pueden bloquear iframes si el sitio no usa HTTPS.
        Solución: habilitar SSL completo.
      error_contenido_no_visible: >
        Algunos temas aplican overflow:hidden. Ajustar CSS o usar plantilla full-width.
      error_pagina_vacia: >
        Revisar que el iframe se haya pegado en modo HTML, no visual.

## 9. Validación Final
### 9.1. Pruebas de funcionamiento

Probar consultas vinculadas a normativa colombiana para validar contextualización.

Realizar análisis de brecha salarial con datos reales para comprobar interpretación correcta de CSV y coherencia del modelo.

Probar preguntas generales de DEI para verificar estabilidad del comportamiento.

### 9.2. Criterios de revisión de respuestas

Coherencia con la normativa colombiana y políticas públicas.

Ausencia de alucinaciones o información no verificada.

Uso efectivo del RAG y de los documentos cargados.

Respeto por los principios del persona y las guidelines configuradas.

## 10. Mantenimiento
### 10.1. Actualización de datos

Actualizar la información cuando existan cambios en nómina, estructuras salariales o políticas de la empresa.

Subir nuevas versiones de documentos y normativas cuando sean modificadas o reemplazadas.

### 10.2. Revisión de procesamiento documental

Revisar y parsear nuevamente documentos complejos antes de cargarlos en Thinkstack.

Verificar que los nuevos documentos cumplen con el estándar de legibilidad requerido.

### 10.3. Gestión de datasets

Documentar cambios en columnas o estructura de los CSV.

Revisar que los parámetros y formatos permanezcan consistentes para evitar confusión del modelo.

### 10.4. Control de calidad del chatbot

Revisar periódicamente las respuestas generadas.

Ajustar prompts, guidelines o estructura si aparecen desviaciones, sesgos o inconsistencias.

## 11. Conclusión

El asistente IA con enfoque DEI es un sistema que depende directamente de:

La calidad, claridad y estructura de los datos cargados.

Un pipeline robusto de curaduría, parsing y normalización documental.

Una configuración precisa del persona, las guidelines y el RAG dentro de Thinkstack.

Cuando estos elementos se mantienen, el asistente IA ofrece respuestas consistentes, contextualizadas y alineadas con los principios de DEI en Colombia.

## 12. Glosario Técnico
### Agente (Agent)

Entidad basada en IA configurada para actuar con un propósito específico. Un agente combina un persona, un conjunto de instrucciones (guidelines) y acceso a fuentes de datos para responder de manera consistente y especializada.

### Asistente (Assistant)

Interfaz conversacional que permite al usuario interactuar con un agente. En este proyecto, El chatbot IA es el asistente que recibe preguntas y produce respuestas basadas en su configuración y datos cargados.

### Curaduría de documentos

Proceso de selección, filtrado y organización de la documentación que será utilizada por el modelo. Incluye eliminar redundancias, priorizar versiones actuales y asegurar relevancia temática.

### Dataset

Conjunto de datos estructurados (por ejemplo, CSV) utilizados por el modelo para análisis cuantitativos, como brechas salariales, estructura organizacional o perfiles laborales.

### Embedding

Representación numérica de textos utilizada por modelos de IA para calcular similitud semántica. Es la base del funcionamiento del RAG.

### Guidelines

Conjunto de reglas formales que definen cómo debe responder el agente: formato, tono, estructura, límites y comportamiento ético. Aseguran consistencia y control sobre el modelo.

### Iframe

Elemento HTML que permite insertar contenido externo dentro de un sitio web (en este caso, Thinkstack dentro de WordPress).

### LlamaParse

Herramienta de parsing impulsada por IA que permite extraer texto estructurado a partir de PDFs complejos que contienen tablas, diagramas, flujos u otros elementos no lineales.

### LLM (Large Language Model)

Modelo de lenguaje avanzado capaz de comprender y generar texto natural. DALIA utiliza un LLM dentro de Thinkstack para responder preguntas basadas en datos y documentos cargados.

### Parsing

Proceso mediante el cual un documento complejo (PDF, imagen, tabla incrustada, etc.) se convierte en texto estructurado legible por un modelo de IA. Es esencial cuando los documentos contienen tablas, flujos o contenido no lineal.

### Persona (Agent Persona)

Identidad profesional asignada al agente que define su perspectiva, tono y área de experticia. En el asistente IA, el persona es una experta en DEI con enfoque en Colombia.

### Pipeline

Conjunto ordenado de pasos técnicos necesarios para preparar datos antes de cargarlos al sistema: curaduría, parsing, normalización y documentación.

### RAG (Retrieval-Augmented Generation)

Técnica donde el modelo busca información relevante en los documentos previamente cargados y luego genera una respuesta fundamentada. Permite que un LLM responda usando datos específicos de una organización.

### Thinkstack

Plataforma utilizada en este proyecto para construir el chatbot. Proporciona gestión de documentos, RAG, configuración del agente, interfaz de conversación y generación del iframe para integración en WordPress.

### Token

Unidad mínima de texto que los LLM procesan (palabras o partes de palabras). Los límites de token influyen en cuánta información puede analizar el modelo en una sola respuesta.

### Vectorización

Transformación de documentos o fragmentos de texto en vectores numéricos para ser indexados y comparados por similitud dentro del sistema RAG.

### WordPress

CMS (Content Management System) utilizado para desplegar DALIA mediante la inserción del iframe generado por Thinkstack.


