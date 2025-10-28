# Etiquetado Inteligente: Predicción Automática de Flairs en Reddit

Este repositorio contiene el código y la documentación del Trabajo de Fin de Grado (TFG) centrado en la **clasificación automática de *flairs* (etiquetas) en publicaciones de Reddit**, utilizando técnicas de Procesamiento del Lenguaje Natural (NLP) y Aprendizaje Supervisado (Machine Learning).

El foco principal es el subreddit `r/mentalhealth`, una de las comunidades más grandes de habla inglesa para la discusión y el apoyo en salud mental.

## Descripción del Problema

Reddit, un híbrido entre red social y foro, permite a los usuarios participar en comunidades específicas llamadas *subreddits*. En `r/mentalhealth`, los usuarios comparten experiencias, buscan apoyo, hacen consultas o reflexionan sobre su bienestar emocional.

Para organizar el contenido, Reddit utiliza *flairs* (etiquetas) que clasifican la naturaleza de una publicación (p.ej., `Need Support`, `Good News`, `Thoughts / Opinions`). Actualmente, este proceso de etiquetado es **manual, subjetivo y heterogéneo**. Esto genera una alta cantidad de publicaciones sin *flair* o con un *flair* incorrecto, dificultando la moderación y la búsqueda de información para los usuarios.

## Objetivos

Este proyecto busca responder a la pregunta: *¿Es posible aplicar técnicas de inteligencia artificial para mejorar la organización y comprensión del discurso sobre la salud mental en este tipo de plataformas?*

Los objetivos principales son:

* **Proponer una metodología** para la clasificación automatizada de *flairs* en `r/mentalhealth` mediante NLP y aprendizaje supervisado.
* **Construir y evaluar modelos** capaces de interpretar el contenido emocional y contextual del lenguaje informal de Reddit.
* **Contribuir a la accesibilidad** y estructuración de las comunidades virtuales de bienestar psicológico.
* **Facilitar el trabajo** de moderadores, investigadores y usuarios finales.
* **Promover el uso ético** y responsable de la IA en plataformas de salud mental.

## Contexto: Psiquiatría Computacional

Este trabajo se enmarca en la **psiquiatría computacional**, un campo emergente que aplica técnicas de NLP y modelos estadísticos para ofrecer nuevas herramientas de monitoreo y evaluación en salud mental. Si bien estas herramientas no sustituyen el diagnóstico médico, tienen un gran valor como sistemas de apoyo y detección temprana.

## 🔧 Metodología

La tarea se define como un problema de **clasificación de texto multiclase**, donde el objetivo es predecir una categoría discreta (el *flair*) a partir del texto de la publicación.

El *pipeline* general del proyecto incluye:

1.  **Adquisición de Datos:** Recolección de un corpus de publicaciones de `r/mentalhealth` (probablemente usando la API de Reddit).
2.  **Preprocesamiento de Texto:** Limpieza y normalización de los datos textuales (tokenización, lematización, manejo de *stopwords*, etc.).
3.  **Ingeniería de Características:** Transformación del texto en vectores numéricos (p.ej., TF-IDF, Word Embeddings).
4.  **Modelado:** Entrenamiento y validación de diversos algoritmos de aprendizaje supervisado (p.ej., Naive Bayes, SVM, Redes Neuronales).
5.  **Evaluación:** Medición del rendimiento del modelo utilizando métricas de clasificación (Accuracy, F1-Score, Matriz de Confusión).

## Desafíos

Reddit presenta ventajas (alto volumen de datos, anonimato relativo, estructura temática) pero también desafíos significativos:

* Lenguaje informal y coloquial.
* Presencia de errores gramaticales y *slang*.
* Uso de sarcasmo e ironía, difíciles de interpretar para un modelo.
* Posible desequilibrio entre las categorías de datos (algunos *flairs* son mucho más comunes que otros).

## Consideraciones Éticas

El análisis de publicaciones sobre salud mental requiere precauciones adicionales.

> **Importante:** Este proyecto maneja datos sensibles. Se adhiere estrictamente a los principios de **transparencia, anonimato y respeto por los usuarios** , incluso si los datos se obtienen de fuentes públicas.
>
> Las herramientas desarrolladas **no deben considerarse un sustituto del diagnóstico médico profesional**. Su valor es como sistema de apoyo a la decisión o detección temprana.


## Stack Tecnológico (Sugerido)


* **Lenguaje:** Python 3.9+
* **Análisis/Procesamiento:** Pandas, NumPy, Scikit-learn
* **NLP:** NLTK
* **Entorno:** VS Code
