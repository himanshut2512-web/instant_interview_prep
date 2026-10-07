from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "genai",
    "name": "NLP & Generative AI",
    "keywords": ["nlp", "natural language", "text", "llm", "llms", "large language model", "generative ai",
                 "genai", "gen ai", "gpt", "rag", "retrieval", "langchain", "llamaindex", "prompt engineering",
                 "embeddings", "vector", "chatbot", "agents", "agentic", "transformers", "bert", "openai",
                 "azure openai", "claude", "fine-tuning"],
    "core": ["generative ai", "genai", "gen ai", "llm", "llms", "rag", "nlp"],
    "subtopics": ["Tokenisation & embeddings", "Transformers & LLMs", "Prompt engineering", "RAG pipelines",
                  "Evaluation & hallucinations", "Fine-tuning (LoRA)", "Agents & tool use", "Cost, latency & guardrails"],
    "revision": note(
        summary="GenAI interviews focus on building reliable LLM applications: how LLMs work at a high level, "
        "prompting, retrieval-augmented generation, evaluation, hallucination control, fine-tuning trade-offs, "
        "agents/tool use and running it all within cost, latency and safety limits.",
        concepts=[
            ("Tokenisation", "Text is split into sub-word tokens (BPE/WordPiece); cost, context limits and "
             "latency are measured in tokens."),
            ("Embeddings", "Dense vectors where semantically similar text is close (cosine similarity) - the basis "
             "of semantic search."),
            ("LLM training stages", "Pre-training (next-token prediction on huge corpora) -> instruction tuning -> "
             "preference tuning (RLHF/DPO)."),
            ("Prompting", "Clear instructions, role/system prompt, few-shot examples, step-by-step reasoning, "
             "structured (JSON) outputs."),
            ("RAG", "Retrieve relevant chunks from your own data and put them in the prompt so answers are grounded, "
             "current and citable."),
            ("Chunking", "Split documents into retrievable units (by headings/semantics, 200-800 tokens with "
             "overlap) - often the biggest lever on RAG quality."),
            ("Hybrid search & reranking", "Combine keyword (BM25) and vector search; rerank top candidates with a "
             "cross-encoder."),
            ("Hallucination", "Fluent but unsupported output - reduce with grounding, citations, abstaining, "
             "verification and evaluation."),
            ("LoRA / PEFT", "Fine-tune a small set of low-rank adapter weights instead of the full model."),
            ("Agents", "An LLM in a loop that plans and calls tools (search, SQL, APIs) and observes results."),
        ],
        explanation=md("""
            **Choosing the approach.**

            | Need | Start with |
            |---|---|
            | Task can be described with instructions | Prompting (+ few-shot examples) |
            | Answers must use private/fresh documents | RAG |
            | Consistent style/format or narrow skill at scale | Fine-tuning (LoRA) after prompting/RAG |
            | Multi-step work using systems | Agent with well-defined tools |

            **RAG pipeline.** Ingest -> clean -> chunk (respect structure, add metadata like title/date/source) ->
            embed -> index in a vector store -> at query time: rewrite/expand query -> hybrid retrieve top-k ->
            rerank -> build a prompt with instructions + context + citations -> generate -> post-process
            (validate citations, guardrails).

            **Evaluation is the differentiator.** Build a golden set of real questions with expected answers and
            source documents. Measure retrieval (recall@k, MRR - did we fetch the right chunk?) separately from
            generation (faithfulness/groundedness, answer relevance, correctness) using human review plus
            LLM-as-judge with a rubric. Track online signals (thumbs up/down, escalation rate) after launch.

            **Reducing hallucinations.** Ground answers in retrieved context, instruct the model to cite sources
            and say "I don't know" when context is insufficient, constrain output formats, lower temperature for
            factual tasks, add verification steps, and fix retrieval first - most "hallucinations" in RAG are
            retrieval misses.

            **Production concerns.** Latency (streaming, smaller/faster models for simple steps, caching), cost
            (token budgets, prompt caching, model routing), safety (PII redaction, prompt-injection defences:
            treat retrieved text as data, least-privilege tools), and observability (log prompts, retrieved chunks,
            outputs and feedback).
        """),
        code=md("""
            import numpy as np

            def top_k_chunks(query_vec, chunk_vecs, chunks, k=4):
                # cosine similarity = dot product of L2-normalised vectors
                q = query_vec / np.linalg.norm(query_vec)
                m = chunk_vecs / np.linalg.norm(chunk_vecs, axis=1, keepdims=True)
                scores = m @ q
                best = np.argsort(-scores)[:k]
                return [(chunks[i], float(scores[i])) for i in best]

            def build_prompt(question, retrieved):
                context = "\\n\\n".join(f"[{n}] {c}" for n, (c, _) in enumerate(retrieved, 1))
                return (
                    "Answer using ONLY the context below. Cite sources like [1]. "
                    "If the answer is not in the context, say you don't know.\\n\\n"
                    f"<context>\\n{context}\\n</context>\\n\\nQuestion: {question}"
                )
        """),
        language="python",
        pitfalls=[
            "Fixed-size chunking that splits tables or sections mid-sentence.",
            "Evaluating only with a few hand-picked demo questions.",
            "Blaming the LLM for wrong answers when retrieval failed to fetch the right chunk.",
            "Putting secrets or excessive tool permissions within reach of prompt injection.",
            "Fine-tuning to add knowledge that changes often (use RAG instead).",
        ],
        tips=[
            "Describe one GenAI project end to end: use case, architecture, evaluation, results, lessons.",
            "Always separate retrieval quality from generation quality when discussing RAG issues.",
            "Quantify: answer accuracy on a golden set, latency p95, cost per query.",
            "Mention guardrails and responsible-AI considerations proactively.",
        ],
        cheat_sheet=[
            "Temperature ~0-0.3 for factual/extraction tasks, higher for creative ones.",
            "Context window = prompt + output tokens; long context is not a substitute for good retrieval.",
            "Recall@k: share of questions whose relevant chunk is in the top k results.",
            "Reciprocal rank fusion: score = sum(1 / (60 + rank)) across rankers.",
            "LoRA trains low-rank matrices A and B so that delta-W = B A; base weights stay frozen.",
            "Prompt injection: instructions hidden in retrieved/user content - treat such content as data.",
        ],
        likely_questions=[
            "Explain RAG and its components.",
            "How do you reduce hallucinations?",
            "How would you evaluate an LLM/RAG application?",
            "RAG vs fine-tuning - when would you use each?",
            "What chunking strategy would you use and why?",
        ],
    ),
    "theory": [
        T("beginner", "What are tokens and embeddings, and why do they matter when building LLM applications?",
          """
          **Tokens** are the units an LLM reads and writes - usually sub-word pieces produced by algorithms like
          Byte-Pair Encoding ("interviewing" might be "interview" + "ing"). Everything practical is measured in
          tokens: the context-window limit, the API cost, and latency (output tokens are generated one at a time).
          Roughly, 1 token is about 3/4 of an English word.

          **Embeddings** are dense numeric vectors representing meaning: texts with similar meaning have vectors that
          point in similar directions, measured with cosine similarity. They power semantic search, clustering,
          deduplication and the retrieval step in RAG.

          Practical implications: keep prompts lean to control cost, chunk documents by tokens, and choose an
          embedding model that fits the language/domain and is used consistently for both documents and queries.
          """,
          ["Sub-word tokenisation", "Tokens drive cost/limits/latency", "Embeddings capture meaning",
           "Cosine similarity & semantic search"],
          "Connect both concepts to cost and retrieval quality - that shows applied understanding.",
          ["How would you count tokens before sending a request?", "Why must queries and documents use the same "
           "embedding model?"], hot=True),
        T("beginner", "What is Retrieval-Augmented Generation (RAG), and why use it?",
          """
          RAG combines a **retriever** with a **generator**: for each question we search our own knowledge base,
          put the most relevant passages into the prompt, and ask the LLM to answer using that context.

          Why: LLMs don't know private or recent information and can hallucinate. RAG makes answers **grounded,
          current and citable** without retraining the model, and access control can be applied at retrieval time.

          Pipeline:
          1. **Ingest** documents, clean them, split into chunks with metadata.
          2. **Embed** chunks and store them in a vector index (FAISS, pgvector, Pinecone, Azure AI Search...).
          3. At query time, **retrieve** top-k chunks (often hybrid keyword + vector search, then rerank).
          4. **Generate** the answer with instructions to cite sources and abstain when unsure.
          5. **Evaluate & monitor** retrieval and answer quality.
          """,
          ["Retriever + generator", "Why: grounding, freshness, citations", "End-to-end pipeline", "Evaluation step"],
          "Describe your own RAG build if you have one - name the vector store, chunk size and the measured gain.",
          ["What chunk size would you choose?", "What is reranking?", "How do you handle access control?"], hot=True),
        T("intermediate", "How do you reduce hallucinations in an LLM application?",
          """
          1. **Ground the model**: RAG with good retrieval; the instruction "answer only from the context, cite
             sources, say you don't know otherwise".
          2. **Fix retrieval first**: many hallucinations are retrieval misses - improve chunking, hybrid search,
             reranking, query rewriting.
          3. **Constrain outputs**: structured outputs/JSON schemas, enumerated choices, lower temperature for
             factual tasks.
          4. **Verify**: post-generation checks - citation validation, a second-pass "is every claim supported by
             the context?" check, or rule-based validators for numbers/IDs.
          5. **Design the UX for uncertainty**: show sources, confidence, and a path to a human.
          6. **Measure**: a golden question set with faithfulness scoring (human + LLM-as-judge), tracked on every
             change; monitor user feedback in production.
          """,
          ["Grounding + abstention", "Retrieval improvements", "Output constraints", "Verification layer",
           "Evaluation & monitoring"],
          "Lead with 'most RAG hallucinations are retrieval problems' - it is an experienced-practitioner insight.",
          ["How would you detect a hallucination automatically?", "Does lowering temperature eliminate hallucinations?"],
          hot=True),
        T("intermediate", "What prompt-engineering techniques do you rely on in production?",
          """
          - **Clear role and task** in a system prompt; state the audience, constraints and what *not* to do.
          - **Context separation** with delimiters/XML tags so instructions and data don't mix (also helps against
            prompt injection).
          - **Few-shot examples** that show the exact format and edge cases.
          - **Step-by-step reasoning** for complex tasks, or splitting the task into a chain of smaller prompts.
          - **Structured outputs** (JSON schema / tool calling) so downstream code can parse reliably.
          - **Explicit fallback behaviour**: "If information is missing, reply 'NOT_FOUND'".
          - **Parameters**: low temperature for extraction/classification; higher for ideation.
          - **Versioning and evaluation**: prompts live in code with tests against a golden set, so changes are
            measured, not guessed.
          """,
          ["Structure of a good prompt", "Few-shot & reasoning", "Structured outputs", "Prompt evaluation/versioning"],
          "Show a before/after prompt from your work and the metric it moved.",
          ["How do you defend against prompt injection?", "When would you chain prompts instead of one big prompt?"]),
        T("advanced", "How would you evaluate a RAG system before and after launch?",
          """
          **Offline (before launch)**
          - Build a **golden dataset**: 100-300 real user questions with reference answers and the source documents
            that contain them, including unanswerable questions.
          - **Retrieval metrics**: recall@k / hit rate (is the right chunk in top-k?), MRR/nDCG (is it ranked
            high?), context precision (how much retrieved text is relevant?).
          - **Generation metrics**: faithfulness/groundedness (claims supported by context), answer relevance,
            correctness vs reference, citation accuracy, correct abstention on unanswerable questions.
          - Use **LLM-as-judge** with a clear rubric for scale, calibrated against human ratings on a sample.
          - Run the suite on every change (chunking, prompt, model) - regression testing for prompts.

          **Online (after launch)**
          - User feedback (thumbs, edits), escalation-to-human rate, deflection rate, latency p95, cost per query.
          - Sample conversations weekly for human review; feed failures back into the golden set.
          - A/B test major changes on business metrics.
          """,
          ["Golden dataset incl. unanswerable", "Separate retrieval and generation metrics", "LLM-as-judge calibrated",
           "Regression testing", "Online metrics & feedback loop"],
          "Mention frameworks (e.g. RAGAS-style metrics) but focus on the methodology, not the tool.",
          ["How do you trust an LLM judge?", "What would you do if recall@5 is only 60%?"], hot=True),
        T("advanced", "Prompting vs RAG vs fine-tuning - how do you decide, and how does LoRA work?",
          """
          - **Prompting** first: cheapest, fastest to iterate; good when the model already has the skill.
          - **RAG** when answers need **knowledge** that is private, large or changing - documents, policies,
            product data. Updating knowledge = re-indexing, no retraining; supports citations and access control.
          - **Fine-tuning** when you need a **behaviour** the prompt can't reliably produce: a strict style or format,
            domain-specific classification/extraction at scale, or distilling a big model's behaviour into a smaller,
            cheaper one. It's poor at adding frequently changing facts.
          - They combine: a fine-tuned model can still use RAG.

          **LoRA** freezes the base model and learns small low-rank matrices A and B for selected weight matrices,
          so the update is delta-W = B A with rank r much smaller than the layer size. This trains well under 1% of
          the parameters, cuts GPU memory (QLoRA adds 4-bit quantisation of the base model), and lets you swap
          adapters per task.

          Decision factors: data availability (fine-tuning needs hundreds-thousands of quality examples), update
          frequency, latency/cost targets, and evaluation results of the simpler options.
          """,
          ["Knowledge vs behaviour distinction", "When each approach fits", "Combining approaches", "LoRA mechanics"],
          "Use the 'knowledge -> RAG, behaviour -> fine-tuning' rule of thumb, then add nuance.",
          ["What data would you need to fine-tune?", "What is QLoRA?", "What is distillation?"]),
    ],
    "practical": [
        P("beginner", "Build a quick sentiment classifier for product reviews with TF-IDF and logistic regression.",
          """
          DataFrame `reviews` with columns `text` and `label` (1 = positive, 0 = negative), 20k rows.
          Report precision, recall and F1 on a held-out set.
          """,
          ["Split train/test with stratification.", "TF-IDF with unigrams + bigrams.",
           "Logistic regression baseline.", "Classification report and error analysis."],
          "TF-IDF + linear models are a strong, fast, explainable baseline for text classification - always worth "
          "trying before fine-tuning a transformer.",
          """
          from sklearn.feature_extraction.text import TfidfVectorizer
          from sklearn.linear_model import LogisticRegression
          from sklearn.metrics import classification_report
          from sklearn.model_selection import train_test_split
          from sklearn.pipeline import make_pipeline

          X_train, X_test, y_train, y_test = train_test_split(
              reviews["text"], reviews["label"], test_size=0.2, stratify=reviews["label"], random_state=1)

          clf = make_pipeline(
              TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=100_000, sublinear_tf=True),
              LogisticRegression(max_iter=2000, C=4.0),
          )
          clf.fit(X_train, y_train)
          print(classification_report(y_test, clf.predict(X_test), digits=3))
          """, "python",
          "Linear in the number of documents x vocabulary features (sparse).",
          ["Sarcasm and negation ('not good')", "Very short reviews", "Class imbalance"],
          "Mention that bigrams capture negations like 'not good' - a nice detail.",
          ["How would a fine-tuned BERT compare?", "How would you explain predictions?"]),
        P("intermediate", "Implement the retrieval step of a RAG system: chunk documents, embed them and return the "
          "top-k chunks for a question.",
          """
          You have `docs: list[str]` (policy documents) and a function `embed(texts) -> np.ndarray` that returns
          one vector per text. Write `chunk`, `build_index` and `search`.
          """,
          ["Chunk by paragraphs, packing up to ~N words with overlap.", "Embed chunks once; normalise vectors.",
           "Embed the query; cosine similarity via dot product.", "Return top-k with scores and source ids."],
          "Normalising vectors lets one matrix-vector product compute all cosine similarities. Overlap preserves "
          "context that would otherwise be cut at chunk boundaries. Keeping the source id enables citations.",
          """
          import numpy as np

          def chunk(doc_id, text, max_words=200, overlap=40):
              words = text.split()
              step = max_words - overlap
              return [{"doc_id": doc_id, "text": " ".join(words[i:i + max_words])}
                      for i in range(0, max(len(words) - overlap, 1), step)]

          def build_index(docs, embed):
              chunks = [c for i, d in enumerate(docs) for c in chunk(i, d)]
              vecs = embed([c["text"] for c in chunks]).astype("float32")
              vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
              return chunks, vecs

          def search(question, chunks, vecs, embed, k=4):
              q = embed([question])[0].astype("float32")
              q /= np.linalg.norm(q)
              scores = vecs @ q
              top = np.argsort(-scores)[:k]
              return [{**chunks[i], "score": round(float(scores[i]), 3)} for i in top]
          """, "python",
          "Brute force O(n * d) per query; use an ANN index (HNSW/IVF) beyond ~100k chunks.",
          ["Empty documents", "Very long tables or code blocks inside docs", "Duplicate chunks dominating top-k"],
          "Say how you'd evaluate it - recall@k on a set of questions with known source documents.",
          ["How would you add keyword search?", "How do you choose chunk size and overlap?"], hot=True),
        P("advanced", "Combine BM25 keyword results and vector-search results with Reciprocal Rank Fusion (RRF).",
          """
          You get two ranked lists of chunk ids for the same query, e.g.
          `bm25 = ["c7", "c2", "c9", "c4"]`, `vector = ["c2", "c5", "c7", "c1"]`.
          Return a fused ranking.
          """,
          ["RRF uses ranks, not raw scores, so scales don't need calibration.",
           "score(d) = sum over lists of 1 / (k + rank), with k = 60.", "Sum per document and sort descending.",
           "Optionally rerank the fused top-n with a cross-encoder."],
          "Hybrid search catches exact terms (product codes, acronyms) that embeddings miss, and semantic matches "
          "that keywords miss. RRF is a robust, parameter-light way to merge them.",
          """
          from collections import defaultdict

          def reciprocal_rank_fusion(*rankings, k=60, top_n=None):
              scores = defaultdict(float)
              for ranking in rankings:
                  for rank, doc_id in enumerate(ranking, start=1):
                      scores[doc_id] += 1.0 / (k + rank)
              fused = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
              return fused[:top_n] if top_n else fused

          bm25 = ["c7", "c2", "c9", "c4"]
          vector = ["c2", "c5", "c7", "c1"]
          print(reciprocal_rank_fusion(bm25, vector, top_n=5))
          # c2 and c7 rise to the top because both retrievers found them
          """, "python",
          "O(total ranked items) to score plus O(u log u) to sort unique ids.",
          ["Lists of different lengths", "Duplicate ids within one list", "One retriever returning nothing"],
          "Explain why rank-based fusion beats adding raw scores from different systems.",
          ["Where would a cross-encoder reranker fit?", "How would you weight one retriever more?"], hot=True),
    ],
    "scenario": [
        S("beginner", """
          The HR head wants an internal chatbot that answers employee questions about leave, travel and benefits
          policies "in two weeks". The policies are 60 PDFs, some outdated.
          """,
          "How would you approach it?",
          [("Scope", "Pick the top 30-50 real questions and the policy owners; define success."),
           ("Clean data", "Remove outdated versions; keep metadata (policy, version, date, region)."),
           ("Build an MVP", "RAG with structure-aware chunking, citations and an 'I don't know' fallback."),
           ("Evaluate", "Golden question set reviewed by HR before launch."),
           ("Launch safely", "Pilot group, feedback button, escalation to HR, access controls.")],
          """
          Two weeks is realistic for a **focused MVP**, not for "all questions". In the first two days I'd collect
          the 30-50 most common questions from HR tickets and agree success criteria with the HR head - e.g. 90%
          correct answers on those questions, with citations.

          Data hygiene matters more than the model: I'd work with HR to remove outdated PDFs and tag each document
          with policy name, version, date and region. Then a standard RAG build: structure-aware chunking (by
          policy section), embeddings in a vector store, a prompt that answers only from context, cites the policy
          and says "please contact HR" when unsure.

          Before launch, HR reviews answers to the golden questions. We pilot with one department, collect
          thumbs up/down, and escalate unanswered questions to HR - which also tells us which policies to fix.
          """,
          ["Scopes realistically", "Prioritises data quality", "Grounded answers with citations & fallback",
           "Evaluation and safe rollout"],
          ["Promising it will answer everything", "Ignoring outdated documents", "No evaluation before launch"],
          ["How would you handle region-specific policies?", "What metrics would you report after a month?"]),
        S("intermediate", """
          Your RAG assistant for a bank's product documents answers most questions well, but for some it gives
          confident, wrong answers - e.g. quoting the wrong interest rate for a fixed deposit product.
          """,
          "How do you diagnose and fix it?",
          [("Collect failures", "Gather the bad cases into an evaluation set."),
           ("Split the problem", "For each, check whether the right chunk was retrieved (retrieval vs generation)."),
           ("Fix retrieval", "Table-aware chunking, metadata filters, hybrid search, reranking."),
           ("Fix generation", "Grounding + citation instructions, abstain rule, numeric verification."),
           ("Guard & monitor", "Regression tests on the eval set; route rate questions to a structured source.")],
          """
          I'd gather all reported failures and tag each one: was the correct passage in the retrieved top-k?

          If **not retrieved** (usually most cases): rate tables are often split badly by fixed-size chunking, or
          the query "FD rate for 2 years" doesn't match the embedding of a table. Fixes: table-aware chunking that
          keeps each row with its headers, metadata filters (product, effective date), hybrid search so exact terms
          like "2 years" and product codes match, and a reranker on the top 20.

          If **retrieved but answered wrongly**: tighten the prompt (answer only from context, quote the figure
          with its citation, say "I'm not sure" if two figures conflict), and add a verification step that checks
          every number in the answer appears in the cited chunk.

          For high-stakes facts like interest rates, I'd go further and answer from a **structured rates table**
          via a tool/SQL lookup instead of free text. Every fix is tested against the evaluation set before release.
          """,
          ["Separates retrieval from generation errors", "Knows table/chunking issues", "Verification for numbers",
           "Uses structured data for high-stakes facts"],
          ["Just switching to a bigger model", "Lowering temperature and calling it fixed", "No regression testing"],
          ["How would you keep rates up to date?", "How would you measure faithfulness automatically?"], hot=True),
        S("advanced", """
          Your GenAI assistant is a success: usage grew to 10,000 daily users. Monthly LLM costs are 6x over budget
          and p95 latency is 9 seconds. Leadership wants costs cut by 60% without hurting quality.
          """,
          "What is your plan?",
          [("Measure", "Break down cost and latency by step, prompt and query type."),
           ("Cut tokens", "Trim prompts, fewer/smaller chunks, prompt caching for static prefixes."),
           ("Route models", "Small fast model for simple intents; large model only when needed."),
           ("Cache & stream", "Semantic/response caching for repeated questions; stream tokens to the UI."),
           ("Guard quality", "Run the golden-set eval on each change; A/B test before full rollout.")],
          """
          First I'd instrument: tokens, cost and latency per request, split by pipeline step and intent. Usually a
          few things dominate - an oversized system prompt, too many retrieved chunks, and using the largest model
          for every request.

          Then the levers, measured one at a time against the golden-set evaluation:
          1. **Token diet** - shorter prompts, retrieve 4 reranked chunks instead of 12, and **prompt caching**
             for the static system prompt and instructions.
          2. **Model routing** - a small, fast model classifies intent and answers simple/FAQ queries; the large
             model handles complex reasoning only. This alone is often a 50%+ saving.
          3. **Caching** - exact and semantic caches for frequent questions (with invalidation when documents
             change).
          4. **Latency** - stream responses, parallelise retrieval steps, cap output length.

          I'd A/B test the optimised path on 10% of traffic, confirm quality metrics hold (accuracy on golden set,
          thumbs-up rate) and then roll out, reporting cost per conversation and p95 latency weekly.
          """,
          ["Instruments before optimising", "Multiple concrete levers (tokens, routing, caching)",
           "Protects quality with evaluation", "Quantified, staged rollout"],
          ["Switching everything to the cheapest model", "Optimising without measurement", "Ignoring cache invalidation"],
          ["How would you build the router?", "What is semantic caching and its risks?"], hot=True),
    ],
    "quiz": [
        Q("beginner", "In a RAG system, what is the retriever's job?",
          ["Train the LLM on company data", "Find the most relevant chunks of knowledge for the query",
           "Translate the answer", "Reduce the model's temperature"], 1,
          "The retriever searches the indexed knowledge base and supplies relevant context to the generator.",
          ["RAG doesn't retrain the model.", "Correct.", "Not its role.", "Temperature is a generation setting."],
          "Mention that retrieval quality is usually the biggest driver of RAG answer quality.", hot=True),
        Q("beginner", "What does raising the sampling temperature of an LLM do?",
          ["Makes outputs more deterministic", "Makes outputs more random and diverse", "Increases the context window",
           "Reduces cost"], 1,
          "Higher temperature flattens the token probability distribution, so less likely tokens are sampled more often.",
          ["That is lower temperature.", "Correct.", "Unrelated.", "Cost depends on tokens, not temperature."],
          "Use low temperature for extraction and classification tasks."),
        Q("intermediate", "Which technique fine-tunes an LLM by training small low-rank matrices while freezing the "
          "base weights?",
          ["RLHF", "LoRA", "Beam search", "Distillation"], 1,
          "LoRA learns delta-W = B A with low rank, training a tiny fraction of parameters.",
          ["RLHF tunes on human preferences, typically all weights or adapters.", "Correct.", "A decoding strategy.",
           "Trains a smaller student model."],
          "Mention QLoRA for memory-constrained fine-tuning.", hot=True),
        Q("intermediate", "Cosine similarity between two embeddings measures:",
          ["The difference in their lengths", "The angle between them (direction), ignoring magnitude",
           "The number of shared tokens", "Their Euclidean distance"], 1,
          "Cosine similarity is the dot product of normalised vectors - it compares direction only.",
          ["Magnitude is normalised away.", "Correct.", "That's lexical overlap.",
           "Related but not identical unless vectors are normalised."],
          "Normalise vectors once so similarity becomes a fast dot product."),
        Q("advanced", "Your RAG evaluation shows high context recall but low faithfulness. Where is the problem most "
          "likely?",
          ["The retriever misses relevant chunks", "The generator isn't sticking to the retrieved context",
           "The embedding model is wrong", "The vector index is too small"], 1,
          "High context recall means the right information was retrieved; low faithfulness means the answer adds or "
          "distorts claims - a generation/grounding issue.",
          ["Contradicted by high context recall.", "Correct.", "Retrieval is working.", "Retrieval is working."],
          "Fixes: stronger grounding instructions, citations, abstention, verification step.", hot=True),
    ],
}
