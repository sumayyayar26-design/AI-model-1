"""
GrammarGlow AI - Your Personal English Grammar and Writing Coach
================================================================
A single-file Streamlit app. No API keys, no external services, no paid models.

How the "AI / NLP" is built (see the About page for the honest breakdown):
  * Grammar checker ... a rule-based NLP engine (regular expressions + verb
    morphology tables). It is NOT a neural network or generative AI.
  * Lesson search ..... TF-IDF + cosine similarity (scikit-learn).
  * Writing coach ..... text statistics (readability, lexical diversity,
    repetition, passive voice, sentence length).
  * Quiz / vocabulary / challenges ... curated educational content written by hand.

The file is organised in 4 parts:
  1. DATA      - lessons, quiz questions, vocabulary, challenge bank
  2. ENGINE    - grammar rules, checker, writing analysis, sentence rewriting
  3. HELPERS   - session-state progress tracking
  4. UI        - Streamlit pages
Streamlit and Plotly are imported only inside the UI functions, so the engine
(parts 1-2) can be imported and tested without them.
"""
import html
import random
import re
import datetime as dt
from collections import Counter

# =============================================================================
# 1. DATA  (curated educational content)
# =============================================================================
LESSONS = {
    "tenses": {
        "title": "Tenses",
        "rule": "The verb form must match the time of the action. Past time words need past forms; after did/will/can the verb stays in its base form; after have/has/had use the past participle.",
        "explanation": "Tense shows WHEN something happens. Mixing a present verb with a past time word (yesterday, last week, ago) is one of the most common learner mistakes.",
        "details": [
            "Present simple: I study every day. (habits, facts)",
            "Past simple: I studied yesterday. (finished actions)",
            "Future simple: I will study tomorrow. (will + base verb)",
            "Present perfect: I have studied for two hours. (have/has + past participle)",
            "With did: Did you study? (did + base verb, never did + past form)",
        ],
        "examples": ["Yesterday I went to the market. (not: Yesterday I go)", "She has eaten lunch. (not: She has ate lunch)"],
        "practice": ("Correct the sentence: Last night we watch a film.", "Last night we watched a film."),
    },
    "articles": {
        "title": "Articles (a, an, the)",
        "rule": "Use 'a' before a consonant SOUND, 'an' before a vowel SOUND, and 'the' for something specific. Never use 'a/an' before plural nouns.",
        "explanation": "The choice depends on how the next word sounds, not how it is spelled: 'an hour' (silent h) but 'a university' (starts with a 'yu' sound). Singular job titles need an article ('I am a student'). Sports take no article ('play football').",
        "details": [],
        "examples": ["She has an idea and a plan.", "He plays football and works as a teacher."],
        "practice": ("Fill in a/an: She is ___ honest girl.", "an"),
    },
    "prepositions": {
        "title": "Prepositions",
        "rule": "Many verbs, adjectives and time words go with one fixed preposition. Learn them as pairs.",
        "explanation": "Prepositions rarely translate word-for-word from other languages. Learn them with the word: depend ON, interested IN, good AT, married TO, afraid OF.",
        "details": ["on + days/dates: on Friday", "in + months/years/parts of the day: in May, in the morning", "at + clock time / night: at 5 pm, at night", "discuss, enter, reach, marry: NO preposition after them"],
        "examples": ["We discussed the problem. (not: discussed about)", "I am interested in music. (not: interested on)"],
        "practice": ("Correct: I am good in mathematics.", "I am good at mathematics."),
    },
    "subject_verb_agreement": {
        "title": "Subject-Verb Agreement",
        "rule": "A singular subject takes a singular verb (he goes, she is, it has); a plural subject or I/you/we/they takes the plural form (they go, we are, you have).",
        "explanation": "In the present simple, add -s/-es to the verb only for he, she, it and singular nouns. With do/does, only 'does' goes with he/she/it. Some nouns look plural but are singular (news, physics); some plurals do not end in -s (people, children).",
        "details": ["I am / you are / he is / they are", "I have / he has / they have", "I do not / he does not (doesn't)", "The news is good. The children are happy."],
        "examples": ["She likes tea and he drinks coffee.", "The students are in class."],
        "practice": ("Correct: He don't like coffee.", "He doesn't like coffee."),
    },
    "active_passive": {
        "title": "Active and Passive Voice",
        "rule": "Active: the subject does the action (The chef cooked the meal). Passive: the subject receives the action (The meal was cooked by the chef) = be + past participle.",
        "explanation": "Use the passive when the doer is unknown or unimportant, or in formal and scientific writing. Too many passive sentences can make writing heavy, so the Writing Coach points them out.",
        "details": ["Present: writes -> is written", "Past: wrote -> was written", "Future: will write -> will be written", "Present perfect: has written -> has been written"],
        "examples": ["The letter was sent yesterday.", "English is spoken in many countries."],
        "practice": ("Make passive: Tom painted the wall.", "The wall was painted by Tom."),
    },
    "direct_indirect": {
        "title": "Direct and Indirect Speech",
        "rule": "Direct speech repeats the exact words in quotation marks. Indirect speech retells them, usually moving the tense one step back and changing pronouns and time words.",
        "explanation": "With a past reporting verb (said, told) the tense shifts back: am/is -> was, will -> would, can -> could, present simple -> past simple. 'Tomorrow' becomes 'the next day'. Questions lose question word order: 'Where do you live?' -> 'He asked where I lived.'",
        "details": [],
        "examples": ["She said, \"I am tired.\" -> She said that she was tired.", "He said, \"I will come tomorrow.\" -> He said that he would come the next day."],
        "practice": ("Change to indirect: He said, \"I like tea.\"", "He said that he liked tea."),
    },
    "punctuation": {
        "title": "Punctuation",
        "rule": "End every sentence with . ? or !; put a space AFTER a comma, not before it; use apostrophes in contractions (don't, it's).",
        "explanation": "Punctuation shows where ideas begin and end. A question ends with '?', a statement with '.'. Write contractions with an apostrophe: 'dont' is wrong, \"don't\" is right. 'It's' means 'it is'; 'its' shows possession.",
        "details": [],
        "examples": ["Where do you live?", "It's late, so we should go."],
        "practice": ("Correct: She dont like apples", "She doesn't like apples."),
    },
    "capitalization": {
        "title": "Capitalization",
        "rule": "Capitalize the first word of a sentence, the pronoun I, and names of people, places and days.",
        "explanation": "Capital letters mark the start of sentences and special names. The pronoun 'I' is always a capital letter, even in the middle of a sentence.",
        "details": [],
        "examples": ["Today I met Sara in Lahore.", "My exam is on Monday."],
        "practice": ("Correct: i think we can win", "I think we can win."),
    },
    "repeated_words": {
        "title": "Repeated Words",
        "rule": "Do not write the same word twice in a row by accident.",
        "explanation": "Typing 'the the' is a very common slip. Proofread slowly. Also avoid using the same word again and again in a paragraph; use synonyms for variety.",
        "details": [],
        "examples": ["This is the best day. (not: the the best)", "I want to go to the park."],
        "practice": ("Correct: She went to to the market.", "She went to the market."),
    },
    "common_errors": {
        "title": "Common Learner Errors",
        "rule": "Some words are often confused or misspelled: could HAVE (not could of), a lot (not alot), there/their, you're/your. Uncountable nouns have no plural.",
        "explanation": "Uncountable nouns (information, advice, furniture, homework) never take -s and use 'much', not 'many'. Comparatives like 'better' already mean 'more', so do not say 'more better'.",
        "details": [],
        "examples": ["I could have helped you.", "She gave me useful information."],
        "practice": ("Correct: He gave me many informations.", "He gave me much information."),
    },
}

LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Each quiz item: topic, level, question, options, index of correct option, explanation
def _q(topic, level, q, options, answer, explain):
    return {"topic": topic, "level": level, "q": q, "options": options, "answer": answer, "explain": explain}

QUIZ = [
    _q("Tenses", "Beginner", "She ___ to school every day.", ["go", "goes", "going", "went"], 1, "'Every day' shows a habit (present simple). With she/he/it the verb takes -s/-es: goes."),
    _q("Tenses", "Intermediate", "I ___ my homework when the lights went out.", ["did", "was doing", "have done", "do"], 1, "A longer past action interrupted by a shorter one uses the past continuous: was doing."),
    _q("Tenses", "Advanced", "By next June, they ___ the bridge.", ["will finish", "will have finished", "have finished", "finished"], 1, "Future perfect (will have + past participle) shows an action completed before a future time."),
    _q("Articles", "Beginner", "He is ___ engineer.", ["a", "an", "the", "(no article)"], 1, "'Engineer' starts with a vowel sound, so we use 'an'."),
    _q("Articles", "Intermediate", "___ Sun rises in the east.", ["A", "An", "The", "(no article)"], 2, "There is only one Sun, so we use 'the' for unique things."),
    _q("Articles", "Advanced", "He plays ___ guitar, but he doesn't play ___ football.", ["the / (no article)", "a / the", "(no article) / the", "the / the"], 0, "Musical instruments take 'the'; sports take no article."),
    _q("Prepositions", "Beginner", "The meeting is ___ Monday.", ["in", "on", "at", "by"], 1, "Use 'on' with days of the week."),
    _q("Prepositions", "Intermediate", "She is afraid ___ spiders.", ["from", "of", "with", "to"], 1, "The fixed pair is 'afraid of'."),
    _q("Prepositions", "Advanced", "He insisted ___ paying for the dinner.", ["on", "at", "to", "for"], 0, "'Insist on' + -ing form is the correct collocation."),
    _q("Active & Passive", "Beginner", "The cake ___ by my mother.", ["made", "was made", "is make", "making"], 1, "Passive voice = be + past participle. Past tense: was made."),
    _q("Active & Passive", "Intermediate", "Passive of 'They are building a house.'", ["A house is built by them.", "A house is being built by them.", "A house was being built by them.", "A house has been built by them."], 1, "Present continuous passive = is/are being + past participle."),
    _q("Active & Passive", "Advanced", "Passive of 'People say that he is honest.'", ["He is said to be honest.", "He said to be honest.", "He is saying to be honest.", "He was say honest."], 0, "Reporting verbs form the passive: 'He is said to be honest.'"),
    _q("Direct & Indirect", "Beginner", "He said, 'I am happy.' -> He said that he ___ happy.", ["is", "was", "will be", "has been"], 1, "Present tense moves one step back in reported speech: am -> was."),
    _q("Direct & Indirect", "Intermediate", "She asked, 'Where do you live?' -> She asked me where ___.", ["do I live", "I lived", "did I live", "I have lived"], 1, "Reported questions use statement word order and shift the tense back: where I lived."),
    _q("Direct & Indirect", "Advanced", "He said, 'I will call you tomorrow.' -> He said that he ___ me ___.", ["will call / tomorrow", "would call / the next day", "called / tomorrow", "would call / yesterday"], 1, "will -> would and tomorrow -> the next day."),
    _q("Subject-Verb Agreement", "Beginner", "My brother ___ football every Sunday.", ["play", "plays", "playing", "are playing"], 1, "Singular subject (my brother) + present simple needs -s: plays."),
    _q("Subject-Verb Agreement", "Intermediate", "Neither the teacher nor the students ___ ready.", ["is", "are", "has", "was"], 1, "With neither...nor, the verb agrees with the nearer subject (students): are."),
    _q("Subject-Verb Agreement", "Advanced", "The number of applicants ___ increased this year.", ["have", "has", "are", "were"], 1, "'The number of' is singular: has. (Compare: 'A number of applicants have...')."),
    _q("Sentence Correction", "Beginner", "Choose the correct sentence.", ["He don't like tea.", "He doesn't like tea.", "He doesn't likes tea.", "He not like tea."], 1, "He + doesn't + base verb (like)."),
    _q("Sentence Correction", "Intermediate", "Choose the correct sentence.", ["I have went there last year.", "I went there last year.", "I have go there last year.", "I did went there last year."], 1, "'Last year' is a finished past time, so use past simple: went."),
    _q("Sentence Correction", "Advanced", "Choose the correct sentence.", ["Hardly had he arrived when it started to rain.", "Hardly he had arrived when it started to rain.", "Hardly had he arrive when it started to rain.", "Hardly he arrived when it started rain."], 0, "After 'Hardly' at the start, use inversion: had + subject + past participle."),
]
TOPICS = sorted({q["topic"] for q in QUIZ})

# (word, level, part of speech, meaning, example, synonyms, antonyms)
VOCAB = [
    ("diligent", "Beginner", "adjective", "hard-working and careful in one's work", "She is a diligent student who never misses homework.", ["hardworking", "industrious"], ["lazy", "careless"]),
    ("abundant", "Beginner", "adjective", "existing in large quantities", "The region has abundant fresh water.", ["plentiful", "ample"], ["scarce", "rare"]),
    ("scarce", "Beginner", "adjective", "not enough; hard to find", "Food was scarce during the winter.", ["rare", "limited"], ["abundant", "plentiful"]),
    ("genuine", "Beginner", "adjective", "real and honest, not fake", "He showed genuine interest in my project.", ["authentic", "sincere"], ["fake", "false"]),
    ("vivid", "Beginner", "adjective", "very clear, bright or detailed", "She gave a vivid description of the trip.", ["bright", "striking"], ["dull", "vague"]),
    ("reluctant", "Beginner", "adjective", "not willing to do something", "He was reluctant to speak in public.", ["unwilling", "hesitant"], ["eager", "willing"]),
    ("flourish", "Beginner", "verb", "to grow or develop well", "Small businesses flourish in this city.", ["thrive", "prosper"], ["decline", "wither"]),
    ("concise", "Beginner", "adjective", "short and clear, using few words", "Please write a concise summary.", ["brief", "succinct"], ["wordy", "lengthy"]),
    ("candid", "Intermediate", "adjective", "honest and direct, even when it is difficult", "She gave a candid answer about her mistakes.", ["frank", "open"], ["secretive", "evasive"]),
    ("resilient", "Intermediate", "adjective", "able to recover quickly from difficulty", "Children are often more resilient than adults expect.", ["tough", "adaptable"], ["fragile", "weak"]),
    ("versatile", "Intermediate", "adjective", "able to do many different things", "Python is a versatile programming language.", ["flexible", "adaptable"], ["limited", "rigid"]),
    ("plausible", "Intermediate", "adjective", "seeming reasonable or likely to be true", "His explanation sounded plausible.", ["believable", "credible"], ["unlikely", "implausible"]),
    ("inevitable", "Intermediate", "adjective", "certain to happen; cannot be avoided", "Change is inevitable in technology.", ["unavoidable", "certain"], ["avoidable", "uncertain"]),
    ("integrity", "Intermediate", "noun", "being honest and having strong moral principles", "A good leader acts with integrity.", ["honesty", "honour"], ["dishonesty", "corruption"]),
    ("obsolete", "Intermediate", "adjective", "no longer used because something newer exists", "Floppy disks are now obsolete.", ["outdated", "old-fashioned"], ["modern", "current"]),
    ("mitigate", "Intermediate", "verb", "to make something less serious or harmful", "Trees help mitigate the effects of heat.", ["reduce", "lessen"], ["worsen", "aggravate"]),
    ("eloquent", "Advanced", "adjective", "able to speak or write clearly and convincingly", "She gave an eloquent speech.", ["articulate", "expressive"], ["inarticulate", "tongue-tied"]),
    ("ambiguous", "Advanced", "adjective", "having more than one possible meaning", "The instructions were ambiguous.", ["unclear", "vague"], ["clear", "explicit"]),
    ("meticulous", "Advanced", "adjective", "very careful about small details", "He is meticulous about checking his code.", ["thorough", "precise"], ["careless", "sloppy"]),
    ("pragmatic", "Advanced", "adjective", "practical rather than theoretical", "We need a pragmatic solution, not a perfect one.", ["practical", "realistic"], ["idealistic", "impractical"]),
    ("ephemeral", "Advanced", "adjective", "lasting for a very short time", "Social media fame is often ephemeral.", ["fleeting", "temporary"], ["permanent", "lasting"]),
    ("tenacious", "Advanced", "adjective", "determined and not giving up easily", "A tenacious researcher keeps testing ideas.", ["persistent", "determined"], ["weak-willed", "yielding"]),
    ("scrutinize", "Advanced", "verb", "to examine something very carefully", "Auditors scrutinize every financial record.", ["inspect", "examine"], ["ignore", "overlook"]),
    ("benevolent", "Advanced", "adjective", "kind and generous towards others", "The benevolent donor funded new scholarships.", ["kind", "charitable"], ["malevolent", "cruel"]),
]

# (incorrect sentence, correct sentence, topic, explanation)
CORRECTION_TASKS = [
    ("She don't like apples.", "She doesn't like apples.", "Subject-Verb Agreement", "With she/he/it use 'doesn't' + base verb."),
    ("Yesterday we go to the park.", "Yesterday we went to the park.", "Tenses", "'Yesterday' needs the past simple: went."),
    ("I am agree with you.", "I agree with you.", "Tenses", "'Agree' is a verb; do not add 'am'."),
    ("He is good in mathematics.", "He is good at mathematics.", "Prepositions", "The fixed pair is 'good at'."),
    ("I have a idea.", "I have an idea.", "Articles", "'Idea' starts with a vowel sound, so use 'an'."),
    ("They was very happy.", "They were very happy.", "Subject-Verb Agreement", "'They' is plural, so use 'were'."),
]

EXAMPLES = [
    "Yesterday I go to the market. She don't like apples. I have a idea.",
    "He is good in mathematics and he discuss about the problem with his teacher.",
    "i am agree with you but they was very late for the the meeting",
    "My brother play football every Sunday, and he have two friends in in the team.",
    "I could of helped you. She gave me many informations about the exam",
]

# =============================================================================
# 2. ENGINE  (rule-based NLP grammar checker, writing analysis, rewriting)
# =============================================================================
# ---- 2a. verb morphology tables (used by tense and agreement rules) ----------
IRREGULAR = {  # base: (past simple, past participle)
    "go": ("went", "gone"), "eat": ("ate", "eaten"), "see": ("saw", "seen"), "take": ("took", "taken"),
    "write": ("wrote", "written"), "give": ("gave", "given"), "do": ("did", "done"), "buy": ("bought", "bought"),
    "make": ("made", "made"), "come": ("came", "come"), "run": ("ran", "run"), "speak": ("spoke", "spoken"),
    "drink": ("drank", "drunk"), "know": ("knew", "known"), "get": ("got", "got"), "have": ("had", "had"),
    "meet": ("met", "met"), "say": ("said", "said"), "tell": ("told", "told"), "think": ("thought", "thought"),
    "feel": ("felt", "felt"), "bring": ("brought", "brought"), "sit": ("sat", "sat"), "begin": ("began", "begun"),
    "break": ("broke", "broken"), "choose": ("chose", "chosen"), "drive": ("drove", "driven"),
}
REGULAR = ["play", "walk", "watch", "visit", "work", "study", "call", "help", "want", "need", "like", "love",
           "talk", "ask", "start", "finish", "open", "clean", "cook", "listen", "learn", "wash", "stay", "live",
           "discuss", "enjoy", "wait", "use"]


def third_person(v):
    """go -> goes, study -> studies, play -> plays"""
    if v == "have":
        return "has"
    if v.endswith(("s", "sh", "ch", "x", "z", "o")):
        return v + "es"
    if v.endswith("y") and v[-2] not in "aeiou":
        return v[:-1] + "ies"
    return v + "s"


def past_regular(v):
    if v.endswith("e"):
        return v + "d"
    if v.endswith("y") and v[-2] not in "aeiou":
        return v[:-1] + "ied"
    return v + "ed"


BASES = sorted(set(IRREGULAR) | set(REGULAR))
PAST = {v: (IRREGULAR[v][0] if v in IRREGULAR else past_regular(v)) for v in BASES}
THIRD = {v: third_person(v) for v in BASES}
TO_BASE = {}                      # any past or 3rd-person form -> base form
for _v in BASES:
    TO_BASE[PAST[_v]] = _v
    TO_BASE[THIRD[_v]] = _v
PART_FIX = {}                     # wrong form after have/has/had -> past participle
for _v, (_p, _pp) in IRREGULAR.items():
    if _pp != _p:
        PART_FIX[_p] = _pp
    if _pp != _v:
        PART_FIX.setdefault(_v, _pp)
PART_FIX.pop("have", None)

QWORDS = {"what", "where", "when", "why", "who", "whom", "whose", "how", "do", "does", "did", "is", "are",
          "was", "were", "can", "could", "will", "would", "should", "have", "has", "had"}
MODALS_ETC = {"to", "will", "can", "could", "should", "would", "may", "might", "must", "do", "does", "did",
              "don't", "doesn't", "didn't", "not", "let", "lets", "make", "makes", "made", "help", "helps",
              "watch", "see", "hear", "feel", "have", "had", "does", "shall"}
VOWEL_SOUND_WORDS = {"hour", "honest", "honor", "honour", "heir", "honorable"}
CONSONANT_SOUND_WORDS = {"one", "once", "european", "ubiquitous", "utensil", "unicorn"}


def match_case(original, new):
    """Keep the capital letter at the start if the original had one."""
    if original[:1].isupper() and new:
        return new[:1].upper() + new[1:]
    return new


def article_for(word):
    w = word.lower()
    if w in VOWEL_SOUND_WORDS:
        return "an"
    if w in CONSONANT_SOUND_WORDS or w.startswith(("univers", "usu", "util", "user", "use", "unif", "unit", "uniq")):
        return "a"
    return "an" if w[0] in "aeiou" else "a"


# ---- 2b. rule registry --------------------------------------------------------
RULES = []   # (compiled regex, category, handler). handler(match) -> (replacement, message) or None


def rule(pattern, category, handler, flags=re.I):
    RULES.append((re.compile(pattern, flags), category, handler))


def simple(pattern, repl, category, message, flags=re.I):
    """Rule that just rewrites the match using a regex replacement template."""
    def handler(m):
        return match_case(m.group(0), m.expand(repl)), message
    rule(pattern, category, handler, flags)


def _prev_word(m):
    words = re.findall(r"[A-Za-z']+", m.string[:m.start()])
    return words[-1].lower() if words else ""


# --- repeated words
def _repeat(m):
    if m.group(1).lower() in {"had", "that"}:
        return None
    return m.group(1), "This word is repeated by mistake."
rule(r"\b(\w+)\s+\1\b", "repeated_words", _repeat)


# --- articles
def _a_an(m):
    word = m.group(2)
    if word.isupper() and len(word) > 1:      # acronyms such as "an MBA" are skipped
        return None
    if m.group(1) == "A" and m.start() > 0 and not re.search(r"[.!?\n]\s*$", m.string[:m.start()]):
        return None                           # e.g. "Plan A is ..." is not an article
    need = article_for(word)
    if m.group(1).lower() == need:
        return None
    return f"{match_case(m.group(1), need)} {word}", f"Use '{need}' before the word '{word}' because of its first sound."
rule(r"\b(a|an)\s+([A-Za-z]+)", "articles", _a_an)

NOT_PLURAL = {"as", "was", "has", "his", "this", "yes", "always", "sometimes", "perhaps", "less", "its", "us", "does",
              "goes", "plus", "news", "series", "species", "lens", "bus", "gas", "canvas", "atlas", "bias", "chaos",
              "virus", "campus", "bonus", "status", "focus", "genius", "means", "headquarters", "whereas", "across",
              "sports", "savings", "customs", "arms", "clothes", "thanks", "goods"}


def _a_plural(m):
    w = m.group(2)
    if w.lower() in NOT_PLURAL or w.endswith(("ss", "us", "is", "ics", "ous")):
        return None
    singular = w[:-3] + "y" if w.endswith("ies") else w[:-1]
    return f"{m.group(1)} {singular}", "'a/an' goes with a singular noun. Remove the plural -s."
rule(r"\b(a|an)\s+([a-z]{3,}s)\b", "articles", _a_plural, 0)

JOBS = "student|teacher|doctor|engineer|nurse|lawyer|artist|writer|manager|developer|programmer|scientist|farmer|driver|singer|actor|designer|pilot"


def _missing_article(m):
    art = article_for(m.group(2))
    return f"{m.group(1)} {art} {m.group(2)}", f"A singular job title needs an article: '{art} {m.group(2)}'."
rule(rf"\b(I am|he is|she is|you are|this is|that is|it is)\s+({JOBS})\b", "articles", _missing_article)
simple(r"\bplay\s+the\s+(football|cricket|tennis|basketball|chess|hockey|badminton|volleyball)\b", r"play \1", "articles",
       "Sports and games are used without 'the'.")


# --- subject-verb agreement
simple(r"\b(he|she|it)\s+(?:don't|dont|do not)\b", r"\1 doesn't", "subject_verb_agreement",
       "With he/she/it use 'doesn't' (does not).")
_SVA_MAP = {"have": "has", "are": "is", "were": "was"}
rule(r"\b(he|she|it)\s+(have|are|were)\b", "subject_verb_agreement",
     lambda m: (f"{m.group(1)} {_SVA_MAP[m.group(2).lower()]}", "He/she/it takes a singular verb."))
_SVA_PL = {"is": "are", "was": "were", "has": "have"}
rule(r"\b(they|we|you)\s+(is|was|has)\b", "subject_verb_agreement",
     lambda m: (f"{m.group(1)} {_SVA_PL[m.group(2).lower()]}", "They/we/you take a plural verb form."))
rule(r"\bI\s+(is|are|has)\b", "subject_verb_agreement",
     lambda m: ("I am" if m.group(1) in ("is", "are") else "I have", "Use 'I am' / 'I have' with the pronoun I."), 0)


def _sva_base(m):
    if _prev_word(m) in MODALS_ETC:
        return None
    verb = m.group(2).lower()
    about = m.group(3) or ""
    if verb == "discuss":                        # 'discuss about' is also a preposition error
        about = ""
    return f"{m.group(1)} {THIRD[verb]}{about}", f"With '{m.group(1)}' the present-tense verb needs -s/-es: '{THIRD[verb]}'."
rule(rf"\b(he|she|it)\s+({'|'.join(b for b in BASES if b != 'have')})\b(\s+about\b)?", "subject_verb_agreement", _sva_base)


def _sva_third(m):
    subj = m.group(0).split()[0]
    verb = TO_BASE[m.group(0).split()[1].lower()]
    return f"{subj} {verb}", f"With '{subj}' use the base verb '{verb}' (no -s)."
rule(rf"\b(?:(?i:they|we|you)|I)\s+({'|'.join(THIRD[b] for b in BASES if b != 'have')})\b", "subject_verb_agreement", _sva_third, 0)

DET_PLURAL = "the|these|those|my|our|their|many|some|all|two|three|four|five"


def _plural_noun_singular_verb(m):
    noun = m.group(2)
    if noun.lower() in NOT_PLURAL or noun.endswith(("ss", "us", "is", "ics")):
        return None
    new = {"is": "are", "was": "were", "has": "have"}[m.group(3).lower()]
    return f"{m.group(1)} {noun} {new}", f"'{noun}' is plural, so the verb must be '{new}'."
rule(rf"\b({DET_PLURAL})\s+(\w+s)\s+(is|was|has)\b", "subject_verb_agreement", _plural_noun_singular_verb)

PLURAL_OK = {"people", "children", "men", "women", "police", "staff", "feet", "teeth", "mice", "rich", "poor", "best",
             "young", "old", "elderly", "others", "other", "few", "many", "following", "rest", "remaining", "majority",
             "minority", "same", "public", "sick", "wounded", "homeless", "unemployed", "jury", "you", "they", "we", "i",
             "he", "she", "it", "there", "these", "those", "who", "what", "one", "two", "three", "four", "five", "ones"}


def _singular_noun_plural_verb(m):
    noun = m.group(2)
    if noun.lower() in PLURAL_OK or noun.lower().endswith("s"):
        return None
    new = {"are": "is", "were": "was"}[m.group(3).lower()]
    return f"{m.group(1)} {noun} {new}", f"'{noun}' is singular, so the verb must be '{new}'."
rule(r"\b(the|every|each|my|his|her)\s+([a-z]+)\s+(are|were)\b", "subject_verb_agreement", _singular_noun_plural_verb)


# --- tenses (modal/did + wrong form, have + wrong participle, fixed expressions)
def _after_helper(m):
    helper, form = m.group(1), m.group(2).lower()
    if helper.lower() == "to" and form in THIRD.values():
        return None
    base = TO_BASE[form]
    return f"{helper} {base}", f"After '{helper}' use the base form '{base}'."
_helpers = "will|can|could|should|would|may|might|must|to|did|didn't|does|doesn't|do|don't"
rule(rf"\b({_helpers})\s+({'|'.join(sorted(TO_BASE, key=len, reverse=True))})\b", "tenses", _after_helper)


def _participle(m):
    new = PART_FIX[m.group(2).lower()]
    return f"{m.group(1)} {new}", f"After '{m.group(1)}' use the past participle '{new}'."
rule(rf"\b(have|has|had)\s+({'|'.join(sorted(PART_FIX, key=len, reverse=True))})\b", "tenses", _participle)


def _am_agree(m):
    subj = m.group(1).split()[0]
    subj = "I" if subj.lower() == "i" else subj
    s = "agrees" if subj.lower() in ("he", "she") else "agree"
    return f"{subj} {s}", "'Agree' is already a verb; do not use 'am/is/are' before it."
rule(r"\b(I am|he is|she is|we are|they are|you are)\s+agree\b", "tenses", _am_agree)
simple(r"\bsince\s+(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten)\s+(years?|months?|weeks?|days?|hours?)\b",
       r"for \1 \2", "tenses", "Use 'for' with a length of time and 'since' with a starting point.")


def _tense_marker_issues(text):
    """Sentences with a past-time word (yesterday, ago ...) should not use present-tense verbs."""
    issues = []
    marker = re.compile(r"\b(yesterday|last (?:night|week|month|year|summer|weekend)|ago)\b", re.I)
    blockers = re.compile(r"\b(now|today|currently|usually|every|always|often|never)\b", re.I)
    verbs = "|".join(sorted(set(BASES) | set(THIRD.values()), key=len, reverse=True))
    vpat = re.compile(rf"\b(I|we|they|you|he|she)\s+({verbs})\b", re.I)
    for sm in re.finditer(r"[^.!?\n]+[.!?]*", text):
        sentence = sm.group(0)
        if not marker.search(sentence) or blockers.search(sentence):
            continue
        for vm in vpat.finditer(sentence):
            word = vm.group(2).lower()
            base = word if word in PAST else TO_BASE.get(word)
            if base is None or base not in PAST:
                continue
            s, e = sm.start() + vm.start(2), sm.start() + vm.end(2)
            issues.append(dict(start=s, end=e, original=text[s:e], replacement=PAST[base], category="tenses",
                               message=f"This sentence talks about the past, so use the past form '{PAST[base]}'."))
    return issues


# --- prepositions
_D = "monday|tuesday|wednesday|thursday|friday|saturday|sunday"
_M = "january|february|march|april|may|june|july|august|september|october|november|december"
simple(r"\b(discuss|discusses|discussed|discussing)\s+about\b", r"\1", "prepositions", "'Discuss' takes its object directly (no 'about').")
simple(r"\b(depend|depends|depended|depending)\s+of\b", r"\1 on", "prepositions", "The correct pair is 'depend on'.")
simple(r"\bmarried\s+with\b", "married to", "prepositions", "The correct pair is 'married to'.")
simple(r"\b(good|bad|weak|excellent|clever)\s+in\s+(english|maths?|mathematics|science|sports?|writing|speaking|cooking|drawing|singing|grammar|music|chess)\b",
       r"\1 at \2", "prepositions", "Use 'good at' for a skill or subject.")
simple(r"\binterested\s+on\b", "interested in", "prepositions", "The correct pair is 'interested in'.")
simple(r"\b(arrive|arrives|arrived|arriving)\s+to\b", r"\1 in", "prepositions", "Use 'arrive in' (cities/countries) or 'arrive at' (places); never 'arrive to'.")
simple(r"\b(listen|listens|listened|listening)\s+(music|songs?|radio|news)\b", r"\1 to \2", "prepositions", "The correct pair is 'listen to'.")
simple(r"\b(afraid|scared)\s+from\b", r"\1 of", "prepositions", "The correct pair is 'afraid of'.")
simple(r"\bcapable\s+to\b", "capable of", "prepositions", "The correct pair is 'capable of'.")
simple(r"\b(explain|explains|explained|explaining)\s+me\b", r"\1 to me", "prepositions", "Say 'explain something to someone'.")
simple(r"\b(enter|enters|entered|entering)\s+in\s+(the|a|an|my|our|his|her)\b", r"\1 \2", "prepositions", "'Enter' takes its object directly (no 'in').")
simple(rf"\bin\s+({_D})\b(?!')", r"on \1", "prepositions", "Use 'on' with days of the week.")
simple(rf"\bon\s+({_M})\b(?!\s+\d)", r"in \1", "prepositions", "Use 'in' with months.")
simple(r"\bat\s+(?:the\s+)?(morning|afternoon|evening)\b", r"in the \1", "prepositions", "Say 'in the morning/afternoon/evening'.")
simple(r"\bin\s+night\b", "at night", "prepositions", "The fixed phrase is 'at night'.")

# --- common errors
simple(r"\b(could|would|should|must|might)\s+of\b", r"\1 have", "common_errors", "Say 'could have', not 'could of'.")
simple(r"\balot\b", "a lot", "common_errors", "'A lot' is two words.")
simple(r"\byour\s+welcome\b", "you're welcome", "common_errors", "'You're' means 'you are'.")
simple(r"\btheir\s+(is|are)\b", r"there \1", "common_errors", "Use 'there' (not 'their') to say something exists.")
simple(r"\bits\s+(a|an|been|not|going|raining|very|important)\b", r"it's \1", "punctuation", "'It's' (with an apostrophe) means 'it is'.")
simple(r"\bmore\s+(better|easier|bigger|faster|happier|cheaper|smaller|taller|harder)\b", r"\1", "common_errors", "The comparative already means 'more'; do not add 'more'.")
simple(r"\bmany\s+(water|information|money|time|advice|homework|furniture|rice|traffic)\b", r"much \1", "common_errors", "Use 'much' with uncountable nouns.")
simple(r"\bmuch\s+(people|students|books|friends|children|things)\b", r"many \1", "common_errors", "Use 'many' with countable plural nouns.")
rule(r"\bmany\s+(informations|advices|furnitures|equipments|homeworks|luggages)\b", "common_errors",
     lambda m: (f"much {m.group(1)[:-1]}", "Uncountable nouns have no plural and take 'much'."))
rule(r"\b(informations|advices|furnitures|equipments|homeworks|luggages|knowledges)\b", "common_errors",
     lambda m: (match_case(m.group(1), m.group(1)[:-1]), f"'{m.group(1)[:-1]}' is uncountable and has no plural form."))
_CONTR = {"dont": "don't", "doesnt": "doesn't", "didnt": "didn't", "cant": "can't", "wont": "won't", "isnt": "isn't",
          "arent": "aren't", "wasnt": "wasn't", "werent": "weren't", "havent": "haven't", "hasnt": "hasn't",
          "couldnt": "couldn't", "wouldnt": "wouldn't", "shouldnt": "shouldn't"}
rule(r"\b(" + "|".join(_CONTR) + r")\b", "punctuation",
     lambda m: (match_case(m.group(1), _CONTR[m.group(1).lower()]), "A contraction needs an apostrophe."))

# --- capitalisation, spacing and punctuation
rule(r"\bi\b(?!\.)", "capitalization", lambda m: ("I", "The pronoun 'I' is always a capital letter."), 0)


def _sentence_start(m):
    before = m.string[:m.start()].rstrip().lower()
    if before.endswith(("e.g.", "i.e.", "dr.", "mr.", "mrs.", "ms.", "vs.", "etc.")):
        return None
    return m.group(0).upper(), "Start a sentence with a capital letter."
rule(r"(?:^|(?<=[.!?]\s)|(?<=\n))[a-z]", "capitalization", _sentence_start, 0)
rule(r"[ \t]+(?=[,.!?;:])", "punctuation", lambda m: ("", "Remove the space before this punctuation mark."))
rule(r",(?=[A-Za-z])", "punctuation", lambda m: (", ", "Put a space after a comma."))
rule(r"(?<=\S)[ ]{2,}(?=\S)", "punctuation", lambda m: (" ", "Use a single space between words."))


def _end_punct_issue(text):
    t = text.rstrip()
    if not t or not t[-1].isalnum():
        return []
    last_sentence = re.split(r"(?<=[.!?])\s+", t)[-1]
    first = re.findall(r"[A-Za-z']+", last_sentence)[:1]
    mark = "?" if first and first[0].lower() in QWORDS else "."
    return [dict(start=len(t), end=len(t), original="", replacement=mark, category="punctuation",
                 message="End the sentence with a full stop or question mark.")]


# ---- 2c. the checker --------------------------------------------------------
def check(text):
    """Return a list of issue dicts (start, end, original, replacement, category, message)."""
    text = text.replace("\u2019", "'")           # curly apostrophe -> straight (same length, offsets stay valid)
    issues = []
    for pattern, category, handler in RULES:
        for m in pattern.finditer(text):
            out = handler(m)
            if out and out[0] != m.group(0):
                issues.append(dict(start=m.start(), end=m.end(), original=m.group(0), replacement=out[0],
                                   category=category, message=out[1]))
    issues += _tense_marker_issues(text) + _end_punct_issue(text)
    issues.sort(key=lambda i: (i["start"], -(i["end"] - i["start"])))
    final, last_end = [], 0
    for i in issues:                              # drop overlapping suggestions
        if i["start"] >= last_end:
            final.append(i)
            last_end = max(last_end, i["end"])
    return final


def apply_issues(text, issues):
    """Return (corrected text, original HTML with red marks, corrected HTML with green marks)."""
    text = text.replace("\u2019", "'")
    corrected, o_html, c_html, pos = [], [], [], 0
    for i in issues:
        seg = text[pos:i["start"]]
        corrected.append(seg)
        o_html.append(html.escape(seg))
        c_html.append(html.escape(seg))
        tip = html.escape(i["message"], quote=True)
        o_html.append(f'<mark class="bad" title="{tip}">{html.escape(i["original"]) or "&empty;"}</mark>')
        c_html.append(f'<mark class="good" title="{tip}">{html.escape(i["replacement"])}</mark>')
        corrected.append(i["replacement"])
        pos = i["end"]
    tail = text[pos:]
    corrected.append(tail)
    o_html.append(html.escape(tail))
    c_html.append(html.escape(tail))
    br = lambda parts: "".join(parts).replace("\n", "<br>")
    return "".join(corrected), br(o_html), br(c_html)


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text.strip()) if s.strip()]


# ---- 2d. writing coach ------------------------------------------------------
WEAK_WORDS = {"very": "use a stronger adjective (e.g. 'very big' -> 'huge')", "really": "delete it or use a stronger word",
              "good": "try: excellent, effective, beneficial", "bad": "try: poor, harmful, unpleasant",
              "nice": "try: pleasant, kind, enjoyable", "thing": "name the thing precisely", "things": "name the things precisely",
              "stuff": "name the items precisely", "big": "try: large, major, significant", "got": "try: received, became, obtained",
              "lots": "try: many, much, a great number of"}
NOT_PASSIVE = {"tired", "excited", "interested", "worried", "bored", "scared", "surprised", "married", "pleased",
               "concerned", "confused", "satisfied", "prepared", "finished", "used", "supposed", "allowed"}


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def analyze_writing(text):
    """Heuristic writing analysis. Scores are simple indicators, not validated measurements."""
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    sents = split_sentences(text)
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return None
    n_w, n_s = len(words), max(1, len(sents))
    syl = sum(syllables(w) for w in words)
    wps = n_w / n_s
    flesch = 206.835 - 1.015 * wps - 84.6 * (syl / n_w)
    grade = 0.39 * wps + 11.8 * (syl / n_w) - 15.59
    lower = [w.lower().strip("'") for w in words]
    ttr = len(set(lower)) / n_w
    skip = ENGLISH_STOP_WORDS | {"did", "does", "done", "said", "just"}
    content = [w for w in lower if w not in skip and len(w) > 2]
    threshold = 2 if n_w < 60 else 3
    repeated = [(w, c) for w, c in Counter(content).most_common() if c >= threshold][:8]
    lens = [len(re.findall(r"[A-Za-z']+", s)) for s in sents]
    long_s = [s for s, n in zip(sents, lens) if n > 25]
    starters = Counter((re.findall(r"[A-Za-z']+", s) or [""])[0].lower() for s in sents)
    rep_start = [(w, c) for w, c in starters.items() if w and c >= 3]
    weak = Counter(w for w in lower if w in WEAK_WORDS)
    passive = [s for s in sents if any(m.group(2).lower() not in NOT_PASSIVE for m in
               re.finditer(r"\b(am|is|are|was|were|be|been|being)\s+(\w+ed|" + "|".join(sorted({p for _, p in IRREGULAR.values()})) + r")\b", s, re.I))]
    issues = check(text)
    choppy = n_s >= 4 and wps < 8
    scores = {
        "Grammar": clamp(100 - 25 * len(issues) / n_s),
        "Sentence structure": clamp(100 - 15 * len(long_s) - 12 * len(rep_start) - (15 if choppy else 0)),
        "Vocabulary": clamp(100 - 8 * sum(weak.values()) - 10 * len(repeated) + (10 if ttr > 0.7 else 0)),
        "Clarity": clamp(100 - 12 * len(passive) - 15 * len(long_s)),
        "Readability": clamp(flesch),
    }
    feedback = []
    if issues:
        feedback.append(f"Grammar: {len(issues)} possible issue(s) found. Check them in the Grammar Checker.")
    if long_s:
        feedback.append(f"Structure: {len(long_s)} sentence(s) have more than 25 words. Try splitting them in two.")
    if rep_start:
        feedback.append("Structure: several sentences start with '" + "', '".join(w for w, _ in rep_start) + "'. Vary your openings.")
    if choppy:
        feedback.append("Structure: your sentences are very short. Join related ideas with 'and', 'because' or 'so'.")
    if repeated:
        feedback.append("Vocabulary: repeated words: " + ", ".join(f"'{w}' ({c}x)" for w, c in repeated) + ". Use synonyms from the Vocabulary Builder.")
    for w, c in weak.items():
        feedback.append(f"Vocabulary: '{w}' ({c}x) is a weak or vague word; {WEAK_WORDS[w]}.")
    if passive:
        feedback.append(f"Clarity: {len(passive)} sentence(s) may use the passive voice. Use active voice when the doer is important.")
    if flesch < 40:
        feedback.append("Readability: the text is hard to read. Use shorter sentences and simpler words.")
    if not feedback:
        feedback.append("No problems detected by these checks. This does not guarantee the writing is perfect.")
    return dict(words=n_w, sentences=n_s, avg_len=wps, flesch=flesch, grade=grade, ttr=ttr, repeated=repeated,
                long_sentences=long_s, weak=weak, passive=passive, issues=issues, scores=scores, feedback=feedback)


# ---- 2e. sentence improvement (dictionary-based rewriting) -------------------
CONTRACTIONS = {"don't": "do not", "doesn't": "does not", "didn't": "did not", "can't": "cannot", "won't": "will not",
                "isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not", "haven't": "have not",
                "hasn't": "has not", "couldn't": "could not", "wouldn't": "would not", "shouldn't": "should not",
                "i'm": "I am", "you're": "you are", "we're": "we are", "they're": "they are", "it's": "it is",
                "that's": "that is", "there's": "there is", "i've": "I have", "we've": "we have", "they've": "they have",
                "i'll": "I will", "we'll": "we will", "let's": "let us", "what's": "what is"}
STYLES = {
    "Simple English": ([("utilize", "use"), ("utilise", "use"), ("commence", "begin"), ("purchase", "buy"), ("assist", "help"),
                        ("approximately", "about"), ("demonstrate", "show"), ("obtain", "get"), ("require", "need"),
                        ("numerous", "many"), ("sufficient", "enough"), ("additional", "more"), ("however", "but"),
                        ("therefore", "so"), ("furthermore", "also"), ("subsequently", "then"), ("individuals", "people"),
                        ("attempt", "try"), ("terminate", "end"), ("inform", "tell"), ("consequently", "so"),
                        ("nevertheless", "still"), ("regarding", "about"), ("facilitate", "help"), ("prior to", "before"),
                        ("in order to", "to"), ("due to the fact that", "because"), ("a large number of", "many"),
                        ("in the event that", "if"), ("with regard to", "about")], False),
    "Formal English": ([("gonna", "going to"), ("wanna", "want to"), ("gotta", "have to"), ("kids", "children"),
                        ("stuff", "things"), ("a bit", "somewhat"), ("kind of", "somewhat"), ("sort of", "somewhat"),
                        ("hi", "hello"), ("hey", "hello"), ("thanks", "thank you"), ("buy", "purchase"), ("big", "large"),
                        ("really", "very"), ("ask for", "request")], True),
    "Academic English": ([("shows", "demonstrates"), ("showed", "demonstrated"), ("show", "demonstrate"), ("kids", "children"),
                          ("big", "significant"), ("i think", "I believe"), ("in my opinion", "it can be argued that"),
                          ("very important", "crucial"), ("enough", "sufficient"), ("look at", "examine"),
                          ("find out", "determine"), ("try", "attempt"), ("gonna", "going to")], True),
    "Professional English": ([("hi", "hello"), ("hey", "hello"), ("thanks", "thank you"), ("asap", "as soon as possible"),
                              ("fyi", "for your information"), ("i want", "I would like"), ("i need", "I require"),
                              ("can you", "could you"), ("let me know", "please let me know"), ("send me", "please send me"),
                              ("problems", "issues"), ("problem", "issue"), ("fix", "resolve"), ("help", "assist"),
                              ("check", "review"), ("get back to", "respond to"), ("sorry for", "apologize for")], True),
}
SENTENCE_STARTERS = {"Academic English": [("But", "However,"), ("So", "Therefore,"), ("Also", "Furthermore,")]}


def rewrite(text, style):
    """Rewrite with phrase dictionaries. Returns (new_text, list of (before, after))."""
    text = text.replace("\u2019", "'")
    pairs, expand = STYLES[style]
    pairs = list(pairs)
    if expand:
        pairs = [(k, v) for k, v in CONTRACTIONS.items()] + pairs
    changes = []
    for old, new in sorted(pairs, key=lambda p: -len(p[0])):
        pattern = re.compile(r"(?<![\w'])" + re.escape(old) + r"(?![\w'])", re.I)

        def sub(m, new=new):
            changes.append((m.group(0), match_case(m.group(0), new)))
            return match_case(m.group(0), new)
        text = pattern.sub(sub, text)
    for old, new in SENTENCE_STARTERS.get(style, []):
        def sub2(m, old=old, new=new):
            changes.append((old, new))
            return m.group(1) + new
        text = re.sub(r"(^|[.!?]\s+)" + old + r"(?=[\s,])[,]?", sub2, text)
    text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    return text, changes


# ---- 2f. TF-IDF lesson search (real machine-learning-style retrieval) --------
_TFIDF = {}


def search_lessons(query, top=3):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    if not _TFIDF:
        keys = list(LESSONS)
        docs = [" ".join([L["title"], L["rule"], L["explanation"], " ".join(L["details"]), " ".join(L["examples"])])
                for L in LESSONS.values()]
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        _TFIDF.update(keys=keys, vec=vec, mat=vec.fit_transform(docs))
    sims = cosine_similarity(_TFIDF["vec"].transform([query]), _TFIDF["mat"])[0]
    order = sims.argsort()[::-1][:top]
    return [(_TFIDF["keys"][i], float(sims[i])) for i in order if sims[i] > 0]


# ---- 2g. quiz / vocabulary / challenge helpers ----------------------------
def build_quiz(topic, level, n, rng=random):
    pool = [q for q in QUIZ if (topic == "All topics" or q["topic"] == topic) and (level == "All levels" or q["level"] == level)]
    return rng.sample(pool, min(n, len(pool)))


def vocab_item(entry, rng=random):
    """Build a 'what does this word mean?' multiple-choice question from a vocabulary entry."""
    word, _lvl, pos, meaning, example, _syn, _ant = entry
    others = rng.sample([v[3] for v in VOCAB if v[0] != word], 3)
    options = others + [meaning]
    rng.shuffle(options)
    return {"topic": "Vocabulary", "level": entry[1], "q": f"What does '{word}' ({pos}) mean?", "options": options,
            "answer": options.index(meaning), "explain": f"'{word}' means {meaning}. Example: {example}"}


def vocab_quiz(n, level="All levels", rng=random):
    pool = [v for v in VOCAB if level == "All levels" or v[1] == level]
    return [vocab_item(v, rng) for v in rng.sample(pool, min(n, len(pool)))]


def make_challenge(seed=None):
    rng = random.Random(seed)
    kind = rng.choice(["grammar", "correction", "vocabulary"])
    if kind == "grammar":
        return {"kind": kind, "items": [rng.choice(QUIZ)]}
    if kind == "vocabulary":
        return {"kind": kind, "items": [vocab_item(rng.choice(VOCAB), rng)]}
    return {"kind": kind, "task": rng.choice(CORRECTION_TASKS)}


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9' ]", "", s.lower().replace("\u2019", "'")).split())


# =============================================================================
# 3. HELPERS  (session-state progress tracking; nothing is written to disk)
# =============================================================================
def new_log():
    return {"sentences": 0, "checks": 0, "mistakes": Counter(), "quizzes": [], "topic_stats": {},
            "practiced": Counter(), "words_seen": set()}


def get_log():
    import streamlit as st
    if "log" not in st.session_state:
        st.session_state.log = new_log()
    return st.session_state.log


def record_check(text, issues):
    log = get_log()
    log["checks"] += 1
    log["sentences"] += len(split_sentences(text))
    for i in issues:                       # only counts are stored, never the text itself
        log["mistakes"][i["category"]] += 1


def record_quiz(label, items, results):
    log = get_log()
    log["quizzes"].append({"label": label, "score": sum(results), "total": len(results)})
    for q, ok in zip(items, results):
        s = log["topic_stats"].setdefault(q["topic"], [0, 0])
        s[0] += int(ok)
        s[1] += 1
        log["practiced"][q["topic"]] += 1


# =============================================================================
# 4. UI  (Streamlit pages)
# =============================================================================
CSS = """
<style>
.stApp {background: linear-gradient(135deg,#f3eeff 0%,#e4d9ff 55%,#f7ebff 100%);}
section[data-testid="stSidebar"] {background: linear-gradient(180deg,#4c2fb3 0%,#7c5cff 100%);}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {color:#fff !important;}
html, body, [class*="css"] {font-family: "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;}
.hero {background: linear-gradient(120deg,#5b3cc4,#8e6bf0 60%,#c9a7ff); color:#fff; border-radius:24px;
       padding:38px 42px; margin-bottom:22px; box-shadow:0 10px 30px rgba(91,60,196,.25);}
.hero h1 {color:#fff; font-size:2.6rem; margin:0 0 6px 0;}
.hero p {color:#f1eaff; font-size:1.15rem; margin:0;}
.card {background:#fff; border-radius:18px; padding:18px 20px; margin-bottom:14px; border:1px solid #e9defc;
       box-shadow:0 4px 14px rgba(124,92,255,.10); color:#2b2350;}
.card h4 {margin:0 0 6px 0; color:#4c2fb3;}
.pill {display:inline-block; background:#efe7ff; color:#5b3cc4; border-radius:999px; padding:2px 12px; font-size:.82rem; margin-right:6px;}
mark.bad {background:#fecdd3; color:#9f1239; border-radius:5px; padding:0 4px;}
mark.good {background:#bbf7d0; color:#14532d; border-radius:5px; padding:0 4px;}
div[data-testid="stMetric"] {background:#fff; border-radius:16px; padding:12px 16px; border:1px solid #e9defc;}
.stButton>button[kind="primary"] {background:linear-gradient(90deg,#6d4be0,#9b7bff); border:none; border-radius:12px;}
</style>
"""
PAGES = ["Home", "Grammar Checker", "Learn Grammar", "Writing Coach", "Grammar Quiz", "Vocabulary Builder",
         "Daily Challenge", "Learning Dashboard", "About Project"]
FEATURES = [
    ("Grammar Checker", "Finds errors in tenses, articles, prepositions, agreement and punctuation and explains each one."),
    ("Learn Grammar", "Short lessons with examples, practice, and a TF-IDF search to find the right rule."),
    ("Writing Coach", "Readability, repetition, sentence length, passive voice, and a sentence improver."),
    ("Grammar Quiz", "21 questions across 7 topics and 3 levels, with scores and explanations."),
    ("Vocabulary Builder", "24 curated words with meanings, examples, synonyms, antonyms and quizzes."),
    ("Daily Challenge", "A fresh grammar, correction or vocabulary task every day."),
    ("Learning Dashboard", "Plotly charts of your mistakes, quiz scores and recommended topics."),
    ("100% offline logic", "No API key, no paid service, and your text is never saved."),
]


def card(inner):
    import streamlit as st
    st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)


def lesson_block(key, show_practice=True):
    """Show one lesson: rule, explanation, examples, and a practice question."""
    import streamlit as st
    L = LESSONS[key]
    st.markdown(f"**Rule:** {L['rule']}")
    st.markdown(f"**In simple words:** {L['explanation']}")
    for d in L["details"]:
        st.markdown(f"- {d}")
    st.markdown("**Two examples**")
    for ex in L["examples"]:
        st.markdown(f"- {ex}")
    if show_practice:
        st.markdown(f"**Practice:** {L['practice'][0]}")
        if st.checkbox("Show answer", key=f"ans_{key}_{id(L)}_{st.session_state.get('_ctx', '')}"):
            st.success(L["practice"][1])


# ----- pages ------------------------------------------------------------------
def page_home():
    import streamlit as st
    st.markdown('<div class="hero"><h1>GrammarGlow AI</h1><p>Write Better. Learn Smarter. Speak Confidently.</p></div>',
                unsafe_allow_html=True)
    st.write("Your personal English grammar and writing coach. It does not only correct your text, it **teaches you the rule behind every mistake**. Choose a page in the sidebar to begin.")
    for row in range(0, len(FEATURES), 4):
        cols = st.columns(4)
        for col, (title, desc) in zip(cols, FEATURES[row:row + 4]):
            with col:
                card(f"<h4>{title}</h4><span style='font-size:.93rem'>{desc}</span>")
    st.info("Quick start: open **Grammar Checker**, press **Load example**, then **Check my writing**.")


def load_example():
    import streamlit as st
    st.session_state["chk_text"] = random.choice(EXAMPLES)


def page_checker():
    import streamlit as st
    import pandas as pd
    ss = st.session_state
    st.header("Smart Grammar Checker")
    st.caption("Rule-based NLP engine. It checks tenses, articles, prepositions, subject-verb agreement, capitalization and punctuation.")
    ss.setdefault("chk_text", "")
    st.text_area("Type or paste English text", key="chk_text", height=170, placeholder="Example: Yesterday I go to the market.")
    c1, c2, _ = st.columns([1, 1, 3])
    go_check = c1.button("Check my writing", type="primary")
    c2.button("Load example", on_click=load_example)
    if go_check:
        if not ss.chk_text.strip():
            st.warning("Please type or paste some text first.")
        else:
            try:
                issues = check(ss.chk_text)
                ss.last_check = {"text": ss.chk_text, "issues": issues}
                record_check(ss.chk_text, issues)
            except Exception as exc:                       # keep the app alive on unexpected input
                st.error(f"Sorry, something went wrong while checking: {exc}")
    res = ss.get("last_check")
    if not res:
        return
    issues = res["issues"]
    corrected, o_html, c_html = apply_issues(res["text"], issues)
    m1, m2, m3 = st.columns(3)
    m1.metric("Possible issues", len(issues))
    m2.metric("Sentences", len(split_sentences(res["text"])))
    m3.metric("Words", len(re.findall(r"[A-Za-z']+", res["text"])))
    if not issues:
        st.info("The supported checks found nothing to correct. This does NOT guarantee the text is error-free: the engine only knows the rules listed on the About page.")
        return
    a, b = st.columns(2)
    with a:
        card(f"<h4>Original</h4>{o_html}")
    with b:
        card(f"<h4>Corrected</h4>{c_html}")
    st.caption("Hover over a highlighted word to see why it was changed. Always read the suggestions critically.")
    st.code(corrected, language=None)
    df = pd.DataFrame([{"Original": i["original"] or "(missing)", "Suggestion": i["replacement"],
                        "Topic": LESSONS[i["category"]]["title"], "Why": i["message"]} for i in issues])
    st.dataframe(df, hide_index=True)
    st.subheader("Learn from your mistakes")
    for cat in dict.fromkeys(i["category"] for i in issues):
        with st.expander(f"{LESSONS[cat]['title']} ({sum(1 for i in issues if i['category'] == cat)} issue(s))", expanded=False):
            ss["_ctx"] = "checker"
            lesson_block(cat)


def page_learn():
    import streamlit as st
    ss = st.session_state
    st.header("Learn Grammar")
    q = st.text_input("Ask the rulebook (TF-IDF search)", placeholder="e.g. when do I use a or an?  /  reported speech  /  past participle")
    if q.strip():
        hits = search_lessons(q)
        if hits:
            st.write("Best matches: " + " ".join(f'<span class="pill">{LESSONS[k]["title"]} ({s:.2f})</span>' for k, s in hits), unsafe_allow_html=True)
        else:
            st.caption("No matching lesson found. Try different words.")
    key = st.selectbox("Choose a topic", list(LESSONS), format_func=lambda k: LESSONS[k]["title"])
    card(f"<h4>{LESSONS[key]['title']}</h4>")
    ss["_ctx"] = "learn"
    lesson_block(key, show_practice=False)
    prompt, answer = LESSONS[key]["practice"]
    st.markdown(f"**Practice:** {prompt}")
    typed = st.text_input("Your answer", key=f"typed_{key}")
    if st.button("Check my answer", key=f"btn_{key}"):
        get_log()["practiced"][LESSONS[key]["title"]] += 1
        if norm(typed) == norm(answer):
            st.success("Correct! Well done.")
        else:
            st.error(f"Not quite. A correct answer is: {answer}")


def page_coach():
    import streamlit as st
    import plotly.graph_objects as go
    tab1, tab2 = st.tabs(["Analyse my writing", "Sentence improver"])
    with tab1:
        st.header("Writing Coach")
        st.caption("Statistics-based feedback. The scores are simple indicators, not a validated grade.")
        text = st.text_area("Paste a paragraph", height=200, key="coach_text")
        if st.button("Analyse", type="primary"):
            if not text.strip():
                st.warning("Please paste a paragraph first.")
            else:
                r = analyze_writing(text)
                if r is None:
                    st.warning("No English words found.")
                else:
                    record_check(text, r["issues"])
                    cols = st.columns(5)
                    for col, (name, val) in zip(cols, r["scores"].items()):
                        col.metric(name, f"{val:.0f}/100")
                    left, right = st.columns([1, 1])
                    with left:
                        names = list(r["scores"]) + [list(r["scores"])[0]]
                        vals = list(r["scores"].values()) + [list(r["scores"].values())[0]]
                        fig = go.Figure(go.Scatterpolar(r=vals, theta=names, fill="toself", line_color="#7c5cff"))
                        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), showlegend=False,
                                          margin=dict(l=30, r=30, t=20, b=20), height=320, paper_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig)
                    with right:
                        st.write(f"**Words:** {r['words']}  |  **Sentences:** {r['sentences']}  |  **Avg. words/sentence:** {r['avg_len']:.1f}")
                        st.write(f"**Flesch reading ease:** {r['flesch']:.0f} (higher = easier)  |  **Grade level:** {r['grade']:.1f}")
                        st.write(f"**Lexical diversity (unique/total words):** {r['ttr']:.2f}")
                    st.subheader("Feedback")
                    for f in r["feedback"]:
                        st.markdown(f"- {f}")
                    if r["issues"]:
                        _c, _o, c_html = apply_issues(text, r["issues"])
                        card(f"<h4>Suggested grammar fixes</h4>{c_html}")
    with tab2:
        st.header("Sentence Improver")
        st.caption("Uses phrase dictionaries and contraction rules. It does NOT use generative AI, so it only changes words it knows and cannot restructure sentences.")
        style = st.selectbox("Style", list(STYLES))
        src = st.text_area("Your sentence(s)", height=120, key="rw_text")
        if st.button("Rewrite", type="primary"):
            if not src.strip():
                st.warning("Please type a sentence first.")
            else:
                out, changes = rewrite(src, style)
                card(f"<h4>{style}</h4>{html.escape(out)}")
                if changes:
                    st.write("**Changes made:** " + ", ".join(f"{a} -> {b}" for a, b in dict.fromkeys(changes)))
                else:
                    st.info("No known phrases to change for this style. The text was left as it is.")


def run_mcq(items, key, label):
    """Show multiple-choice questions in a form; after submit show score and explanations."""
    import streamlit as st
    ss = st.session_state
    if key + "_res" not in ss:
        with st.form(key + "_form"):
            picks = [st.radio(f"**{i + 1}.** {q['q']}", q["options"], index=None, key=f"{key}_p{i}") for i, q in enumerate(items)]
            sent = st.form_submit_button("Submit answers", type="primary")
        if sent:
            ok = [p == q["options"][q["answer"]] for p, q in zip(picks, items)]
            ss[key + "_res"] = {"picks": picks, "ok": ok}
            record_quiz(label, items, ok)
            st.rerun()
        return None
    r = ss[key + "_res"]
    score, total = sum(r["ok"]), len(items)
    st.metric("Your score", f"{score} / {total}", f"{100 * score / total:.0f}%")
    st.progress(score / total)
    for i, (q, ok, pick) in enumerate(zip(items, r["ok"], r["picks"])):
        icon = "Correct" if ok else "Incorrect"
        with st.expander(f"{i + 1}. {icon}: {q['q']}", expanded=not ok):
            st.write(f"Your answer: **{pick or 'no answer'}**")
            st.write(f"Correct answer: **{q['options'][q['answer']]}**")
            st.info(q["explain"])
    return score


def page_quiz():
    import streamlit as st
    ss = st.session_state
    st.header("Grammar Quiz")
    c1, c2, c3 = st.columns(3)
    topic = c1.selectbox("Topic", ["All topics"] + TOPICS)
    level = c2.selectbox("Level", ["All levels"] + LEVELS)
    n = c3.slider("Questions", 1, 10, 5)
    if st.button("Start new quiz", type="primary"):
        ss.quiz_id = ss.get("quiz_id", 0) + 1
        ss.quiz_items = build_quiz(topic, level, n)
    if not ss.get("quiz_items"):
        st.info("Choose a topic and level, then press **Start new quiz**. Each topic/level pair has one question, so pick 'All levels' or 'All topics' for longer quizzes.")
        return
    run_mcq(ss.quiz_items, f"quiz{ss.quiz_id}", "Grammar quiz")


def page_vocab():
    import streamlit as st
    ss = st.session_state
    st.header("Vocabulary Builder")
    st.caption("Curated local word list, so it works offline.")
    t1, t2 = st.tabs(["Learn words", "Vocabulary quiz"])
    with t1:
        level = st.selectbox("Level", ["All levels"] + LEVELS, key="vl")
        words = [v for v in VOCAB if level == "All levels" or v[1] == level]
        today = VOCAB[dt.date.today().toordinal() % len(VOCAB)]
        card(f"<h4>Word of the day: {today[0]}</h4><i>{today[2]}</i> - {today[3]}<br>Example: {today[4]}")
        for w, lvl, pos, meaning, ex, syn, ant in words:
            with st.expander(f"{w}  ({pos}, {lvl})"):
                st.write(f"**Meaning:** {meaning}")
                st.write(f"**Example:** {ex}")
                st.write(f"**Synonyms:** {', '.join(syn)}")
                st.write(f"**Antonyms:** {', '.join(ant)}")
                if st.button("I learned this word", key=f"learn_{w}"):
                    get_log()["words_seen"].add(w)
                    st.success("Saved to your dashboard.")
    with t2:
        lv = st.selectbox("Quiz level", ["All levels"] + LEVELS, key="vql")
        if st.button("New vocabulary quiz", type="primary"):
            ss.vq_id = ss.get("vq_id", 0) + 1
            ss.vq_items = vocab_quiz(5, lv)
        if ss.get("vq_items"):
            run_mcq(ss.vq_items, f"vq{ss.vq_id}", "Vocabulary quiz")
        else:
            st.info("Press **New vocabulary quiz** to start.")


def page_daily():
    import streamlit as st
    ss = st.session_state
    st.header("Daily English Challenge")
    if "challenge" not in ss:
        ss.challenge, ss.ch_id = make_challenge(dt.date.today().isoformat()), 0
    if st.button("Try another challenge"):
        ss.ch_id += 1
        ss.challenge = make_challenge()
    ch = ss.challenge
    st.markdown(f'<span class="pill">{ch["kind"].title()} challenge</span>', unsafe_allow_html=True)
    if ch["kind"] == "correction":
        wrong, right, topic, why = ch["task"]
        card(f"<h4>Correct this sentence</h4><b>{html.escape(wrong)}</b>")
        ans = st.text_input("Your corrected sentence", key=f"ch_ans_{ss.ch_id}")
        if st.button("Check answer", type="primary", key=f"ch_btn_{ss.ch_id}"):
            ok = norm(ans) == norm(right)
            record_quiz("Daily challenge", [{"topic": topic}], [ok])
            (st.success if ok else st.error)("Correct!" if ok else f"Not quite. Correct sentence: {right}")
            st.info(why)
            engine_fix = apply_issues(wrong, check(wrong))[0]
            st.caption(f"GrammarGlow's own checker suggests: {engine_fix}")
    else:
        run_mcq(ch["items"], f"daily{ss.ch_id}{ch['kind']}", "Daily challenge")


def page_dashboard():
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    log = get_log()
    st.header("Learning Dashboard")
    st.caption("Stored only in this browser session. Only counts are saved, never your writing.")
    quizzes = log["quizzes"]
    avg = (100 * sum(q["score"] for q in quizzes) / max(1, sum(q["total"] for q in quizzes))) if quizzes else 0
    cols = st.columns(5)
    cols[0].metric("Sentences checked", log["sentences"])
    cols[1].metric("Mistakes found", sum(log["mistakes"].values()))
    cols[2].metric("Quizzes taken", len(quizzes))
    cols[3].metric("Average quiz score", f"{avg:.0f}%")
    cols[4].metric("Words learned", len(log["words_seen"]))
    if not (log["checks"] or quizzes or log["practiced"]):
        st.info("Nothing to show yet. Check some writing or take a quiz and your progress will appear here.")
        return
    palette = ["#7c5cff", "#a78bfa", "#c4b5fd", "#f0abfc", "#93c5fd", "#86efac", "#fcd34d", "#fda4af"]
    left, right = st.columns(2)
    with left:
        if log["mistakes"]:
            df = pd.DataFrame({"Topic": [LESSONS[k]["title"] for k in log["mistakes"]], "Mistakes": list(log["mistakes"].values())})
            fig = px.bar(df, x="Topic", y="Mistakes", title="Mistakes by grammar topic", color="Topic", color_discrete_sequence=palette)
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig)
        else:
            st.caption("No mistakes recorded yet.")
    with right:
        if quizzes:
            df = pd.DataFrame({"Attempt": range(1, len(quizzes) + 1), "Score %": [100 * q["score"] / q["total"] for q in quizzes],
                               "Quiz": [q["label"] for q in quizzes]})
            fig = px.line(df, x="Attempt", y="Score %", markers=True, hover_data=["Quiz"], title="Quiz scores over time", range_y=[0, 105])
            fig.update_traces(line_color="#7c5cff")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig)
        else:
            st.caption("No quizzes taken yet.")
    left, right = st.columns(2)
    with left:
        if log["practiced"]:
            df = pd.DataFrame({"Topic": list(log["practiced"]), "Practice count": list(log["practiced"].values())})
            fig = px.pie(df, names="Topic", values="Practice count", title="Topics practiced", color_discrete_sequence=palette, hole=0.45)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig)
    with right:
        if log["topic_stats"]:
            df = pd.DataFrame({"Topic": list(log["topic_stats"]), "Accuracy %": [100 * c / t for c, t in log["topic_stats"].values()]})
            fig = px.bar(df, x="Topic", y="Accuracy %", title="Quiz accuracy by topic", range_y=[0, 105], color_discrete_sequence=["#9b7bff"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig)
    st.subheader("Recommended topics for improvement")
    recs = [f"{LESSONS[k]['title']}: {c} mistake(s) in your writing" for k, c in log["mistakes"].most_common(3)]
    recs += [f"{t}: quiz accuracy {100 * c / tot:.0f}%" for t, (c, tot) in sorted(log["topic_stats"].items(), key=lambda x: x[1][0] / x[1][1])[:3]
             if c / tot < 0.7]
    for r in recs or ["Great start. Keep practising to unlock personalised recommendations."]:
        st.markdown(f"- {r}")
    if st.button("Reset my progress"):
        st.session_state.log = new_log()
        st.rerun()


def page_about():
    import streamlit as st
    import pandas as pd
    st.header("About GrammarGlow AI")
    st.write("A university project that combines rule-based NLP, TF-IDF retrieval, text statistics and curated teaching content in one Streamlit app. It needs no API key and sends no data to any external service.")
    st.subheader("What powers each feature (honest breakdown)")
    st.table(pd.DataFrame([
        ("Grammar Checker", "Rule-based NLP: regex patterns + verb-form tables + sentence segmentation", "No machine learning, no neural model"),
        ("Learn Grammar search", "TF-IDF + cosine similarity (scikit-learn)", "Searches 10 hand-written lessons"),
        ("Writing Coach", "Text statistics: Flesch score, lexical diversity, repetition, passive detection", "Scores are heuristics, not validated"),
        ("Sentence Improver", "Phrase dictionaries and contraction rules", "Not generative AI; cannot restructure sentences"),
        ("Quizzes, Vocabulary, Challenges", "Curated local content", "21 quiz questions, 24 words, 6 correction tasks"),
        ("Dashboard", "Session-state counters + Plotly charts", "Resets when the browser session ends"),
    ], columns=["Feature", "Technology", "Note"]))
    st.subheader("Limitations")
    st.markdown("- The checker only detects the patterns it was programmed with; many real errors will be missed and a few suggestions may be wrong.\n"
                "- It does not understand meaning or context, and cannot check spelling in general.\n"
                "- The content banks are small and meant for demonstration; extend `QUIZ`, `VOCAB` and `LESSONS` in `app.py` to grow them.\n"
                "- Accuracy has not been formally measured. Do not treat the output as a guarantee.")
    st.subheader("Privacy")
    st.write("Text you enter is processed in memory only. Progress counters live in Streamlit session state and disappear when you close the tab.")


def main():
    import streamlit as st
    st.set_page_config(page_title="GrammarGlow AI", page_icon="✨", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.sidebar.markdown("## ✨ GrammarGlow AI")
    st.sidebar.caption("Write Better. Learn Smarter. Speak Confidently.")
    page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
    st.sidebar.caption("Your text is never saved. Progress lives only in this session.")
    {"Home": page_home, "Grammar Checker": page_checker, "Learn Grammar": page_learn, "Writing Coach": page_coach,
     "Grammar Quiz": page_quiz, "Vocabulary Builder": page_vocab, "Daily Challenge": page_daily,
     "Learning Dashboard": page_dashboard, "About Project": page_about}[page]()


if __name__ == "__main__":
    main()
