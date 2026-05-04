# Выбор стека для RAG (Часть 2, M3)

## Итоговый стек

| Слой | Выбор |
|---|---|
| Язык | Python 3.12 |
| Vector DB | Qdrant (Docker, localhost:6333) |
| Embedding | BAAI/bge-m3 через sentence-transformers |
| Chunking | LangChain RecursiveCharacterTextSplitter (markdown mode) |
| Framework | LangChain |

## Почему Python

Python — де-факто стандарт для ML/AI pipeline. Конкретно для нашей задачи это лучший выбор по трём причинам:

1. **Экосистема ML-first.** `sentence-transformers`, `qdrant-client`, `langchain` — все написаны на Python, с нимтивными API, без обёрток. BGE-M3 загружается одной строкой: `SentenceTransformer('BAAI/bge-m3')`. В Node.js/TypeScript для этого нужен был бы `transformers.js` (ограниченная поддержка моделей) или вызов Python-скрипта через child_process — костыль.

2. **Общий язык с MCP-сервером.** Наш feature-flags MCP (`mcp-feature-flags/server.py`) уже написан на Python + FastMCP. Search-docs MCP из Части 3 тоже будет на Python. Один язык для обоих серверов — меньше контекста, проще дебаг, общие зависимости в requirements.txt.

3. **LangChain и sentence-transformers родные для Python.** LangChain поддерживает TypeScript, но Python-версия полнее, стабильнее и лучше документирована. А `sentence-transformers` вообще существует только для Python. Альтернатива — делать embedding через OpenAI API (REST, любой язык), но мы выбрали BGE-M3 локально, а он требует Python.

TypeScript подошёл бы если бы мы использовали OpenAI embeddings + Pinecone — обе имеют нормальные JS SDK. Но с BGE-M3 локально Python безальтернативен.

## Обоснование выбора компонентов

### Embedding: BGE-M3

Документация proshop_mern на двух языках (русский + английский), тестовые запросы тоже на русском. Это главный ограничивающий фактор.

Сравнение на русском (MIRACL benchmark):
- BGE-M3: 67.8 — лучший результат среди бесплатных
- Cohere multilingual v3: ~65 (близко, но платный API, $0.10/1M токенов)
- OpenAI text-embedding-3-small: 44 (провал на русском)
- Ollama nomic-embed-text: слабее на multilingual

BGE-M3 бесплатный, локальный, без API-ключей, MIT-лицензия. ~500 MB при первом скачивании (разово). Размерность 1024, поддерживает dense + sparse + multi-vector — пригодится для Части 4 (hybrid search).

### Vector DB: Qdrant

Docker уже работает (MongoDB контейнер). Qdrant — одна команда `docker run`, ~50 MB, готов сразу.

- Встроенный веб-дашборд на :6333 — видно коллекции и векторы без доп. инструментов
- Нативная поддержка sparse vectors — прямая дорога к hybrid search (BM25 + vector + RRF) в Части 4
- Отличный Python SDK (`qdrant-client`)
- Фильтрация по метаданным (source_file, type) из коробки

Альтернативы: Weaviate (тяжелее, Java, нет UI локально), pgvector (нужен Postgres + extension), Pinecone (cloud-only, 1 индекс на free tier).

### Chunking: LangChain RecursiveCharacterTextSplitter

300–512 токенов, overlap 20%, режет по разделителям Markdown (`##`, `*`), не рвёт заголовки, сохраняет контекст секции. Ровно то, что описано в `chunking-strategies-guide.md`.

### Framework: LangChain

Один фреймворк покрывает все слои pipeline: чанкинг, Qdrant-интеграцию (`QdrantVectorStore`), query pipeline с retriever + metadata filtering. Альтернатива — LlamaIndex (тяжеловеснее) или прямой SDK (больше glue-кода).

## Setup

```bash
# Vector DB
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant

# Python-зависимости
pip install qdrant-client sentence-transformers langchain langchain-community
```

API-ключи не требуются — всё работает локально.
