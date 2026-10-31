# GrammarGlow AI ✨
**Write Better. Learn Smarter. Speak Confidently.**

An English grammar and writing coach built with Python and Streamlit. It does not only correct text: it explains the rule behind every mistake, then gives you examples and practice. It needs **no API key, no paid service and no external data download**, so it deploys on Streamlit Community Cloud as-is.

## Problem statement
Many English learners get corrections from a tool but never learn *why* something was wrong, so they repeat the same mistakes. Most free tools also hide how they work.

## Objectives
- Detect common grammar mistakes and suggest corrections.
- Explain each mistake in simple English, with the rule, examples and a practice question.
- Analyse longer writing (readability, repetition, structure).
- Provide quizzes, vocabulary practice and a daily challenge.
- Track progress privately in the browser session.

## Features
| Page | What it does |
|---|---|
| Home | Overview and quick start |
| Grammar Checker | Highlights errors, shows original vs corrected text, explains each fix, and opens a mini lesson per mistake type |
| Learn Grammar | 10 lessons with examples and practice, plus a TF-IDF search ("when do I use a or an?") |
| Writing Coach | Scores for grammar, structure, vocabulary, clarity and readability, plus a Sentence Improver (Simple / Formal / Academic / Professional) |
| Grammar Quiz | 21 questions: 7 topics x 3 levels, with scores and explanations |
| Vocabulary Builder | 24 words with meanings, examples, synonyms, antonyms, word of the day and a quiz |
| Daily Challenge | A grammar question, correction task or vocabulary question |
| Learning Dashboard | Plotly charts and recommended topics |
| About Project | Honest technology breakdown and limitations |

## What is "AI/NLP" here? (honest version)
| Part | Technique | Is it machine learning? |
|---|---|---|
| Grammar checker | Rule-based NLP: regular expressions, verb-form tables (go/went/gone, play/plays), sentence segmentation | No. Hand-written rules |
| Lesson search | TF-IDF vectors + cosine similarity (scikit-learn) | Classical information retrieval |
| Writing coach | Flesch reading ease, lexical diversity, repetition and passive-voice detection | Text statistics, heuristic scores |
| Sentence improver | Phrase dictionaries and contraction expansion | No. It is **not** generative AI |
| Quizzes, vocabulary, challenges | Curated local content | No |

The app does **not** use a neural network, a language model or any generative AI, and no accuracy figure has been measured.

## Run locally (Windows, VS Code)
1. Install Python 3.10 or newer from python.org (tick "Add Python to PATH").
2. Put `app.py`, `requirements.txt` and `README.md` in a folder, e.g. `GrammarGlow-AI`, and open it in VS Code (File > Open Folder).
3. Open a terminal (Terminal > New Terminal) and run:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
4. Your browser opens at `http://localhost:8501`.

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload `app.py`, `requirements.txt` and `README.md` to the root.
2. Go to share.streamlit.io, sign in with GitHub and click **Create app**.
3. Select the repository, branch `main`, and main file `app.py`, then click **Deploy**.

No secrets or environment variables are needed.

## Test it with these sentences
| Type this | Expected correction |
|---|---|
| Yesterday I go to the market. | Yesterday I went to the market. |
| She don't like apples. | She doesn't like apples. |
| I have a idea. | I have an idea. |
| He is good in mathematics. | He is good at mathematics. |
| I am agree with you. | I agree with you. |

(The checker also adds a final full stop when one is missing.)

## Demo tips for a presentation
1. Home page: state the problem and the honest AI breakdown.
2. Grammar Checker: load an example, check it, hover over highlights, open a "Learn from your mistakes" lesson.
3. Learn Grammar: search "reported speech" to show TF-IDF.
4. Writing Coach: paste a paragraph with repeated words; show the radar chart.
5. Take a quiz, then show the Dashboard updating.
6. About Project: explain limitations openly.

## Project abstract
GrammarGlow AI is a web-based English learning assistant that combines a rule-based NLP grammar checker, TF-IDF lesson retrieval, text-statistics writing analysis and curated learning content. For every detected error it explains the grammar rule, shows examples and offers a practice question, turning correction into learning. It runs without external APIs and keeps all user data in the browser session.

## Limitations
- The checker only knows the patterns written in `app.py`. It misses many errors (for example "My brother play football") and can occasionally flag correct text. An empty result does **not** mean the text is error-free.
- It does not understand meaning or context and does not do general spell-checking.
- Content banks are small (21 questions, 24 words, 6 correction tasks, 10 lessons). Extend `QUIZ`, `VOCAB`, `LESSONS` and `CORRECTION_TASKS` to grow them.
- Writing scores are heuristics, not validated grades.
- Progress is lost when the browser session ends (by design, for privacy).
- Tested here with the engine and a mocked UI; please run it once locally before presenting.

## Future improvements
- Add a spaCy dependency parser for noun-subject agreement and richer passive detection.
- Train and evaluate a small classifier on a public learner-error corpus and report real accuracy.
- Add LanguageTool as an optional backend.
- Add user accounts or an opt-in export of progress.

## Viva questions (short answers)
1. **Is this generative AI?** No. It is rule-based NLP plus TF-IDF retrieval and statistics.
2. **How does the checker find "She don't"?** A regular expression matches he/she/it followed by don't and suggests "doesn't".
3. **What is TF-IDF?** It weights words by how often they appear in a document and how rare they are across documents; cosine similarity ranks lessons by closeness to the query.
4. **Why not use an API?** To keep it free, offline-capable and easy to deploy.
5. **How do you handle a/an?** By the first *sound*, using small exception lists (hour, university).
6. **What is the Flesch reading ease?** A formula using words per sentence and syllables per word; higher means easier text.
7. **How is privacy handled?** Text is processed in memory; only counters are kept in session state.
8. **What are the main limitations?** Limited rule coverage, no meaning understanding, small content banks.
9. **How would you measure accuracy?** Test on a labelled learner-error corpus and report precision and recall.
10. **How would you improve it?** Add a dependency parser, a trained error classifier, and more content.
