# 🌙 Bedtime Story Generator

A research-backed bedtime story generator for children ages 5–10, built on GPT-3.5-turbo. Stories are generated, evaluated by a structured LLM judge, and revised in a feedback loop until they meet quality standards across seven criteria.

---

## Setup

**Requirements:** Python 3.10+, an OpenAI API key.

```bash
pip install openai
export OPENAI_API_KEY=your_key_here
python bedtime_story.py
```

---

## How It Works

### 1. User Input
The program collects four inputs at the start of each session:
- **Grade** — used to bucket the child into age group 5–7 (K–2) or 8–10 (grades 3–4), which adjusts vocabulary complexity, sentence length, and thematic depth
- **Genre** — sets the world and tone (e.g. animals, ocean, forest, stars)
- **Interests** — personalizes the story's characters and setting
- **Story request** — the specific story prompt for that night

### 2. Story Generation
The generator constructs a detailed prompt incorporating:

- **Story arc** — all stories follow a strict 5-part structure: Setup → Gentle Challenge → Resolution → Wind-Down → Closing Moment
- **Phonetic softness** — inspired by Lois Lowry and Carl-Johan Ehrlin's research, the prompt instructs the model to minimize harsh consonants (fricatives: f, v, th, s, z, sh; affricates: ch, j; plosives: b, p, t, d, k, g) and favor soft sounds (nasals: m, n; liquids: l, r; long vowels)
- **Sleep language** — Ehrlin's technique of embedding sleep-inducing keywords naturally throughout: *sleep now, yawn, drift gently, eyes heavy, cozy, warm, tucked in*
- **Soothing repetition** — gentle repeated phrases (e.g. "and slowly, slowly...") that calm and convince a child toward sleep
- **Warm ending** — inspired by Mem Fox's child-in-the-lap philosophy: every story ends with a hug, "I love you", or a tender gesture designed to make the child turn to the adult reading to them
- **Age-appropriate language development** — for grades K–2, nursery-rhyme-like rhythm and simple sequencing; for grades 3–4, richer vocabulary, gentle inner thoughts, and mild cause-effect reasoning

### 3. LLM Judge Loop
After the initial draft is generated, a separate LLM judge evaluates it against seven scored criteria (1–5 each). A story **passes only when all scores are ≥ 4**.

| Criterion | What It Checks |
|---|---|
| `age_appropriateness` | Vocabulary, themes, sequencing, and cause-effect suit the grade level |
| `calmness` | No scary, stressful, or over-exciting content; arc winds down toward sleep |
| `phonetic_softness` | Harsh consonants minimized; soft nasals, liquids, and long vowels dominate |
| `sleep_language` | Sleep keywords present naturally; soothing repetition used |
| `story_arc` | Clear setup → challenge → resolution → wind-down → warm close |
| `language_development` | Rhythm, sound patterns, and appropriately rich vocabulary |
| `warm_ending` | Loving closing moment that invites child-adult connection |

If the story fails, the judge returns a **specific list of issues** (not just a score). The revision pass targets those issues directly rather than doing a generic polish. The loop runs up to 3 times. If the story still hasn't passed after 3 attempts, the best available version is used.

### 4. User Feedback Revision
After reading the story, the user can request changes in plain language (e.g. *"make the bunny character funnier"* or *"add a rainbow"*). The story is revised accordingly and then re-run through the judge loop before being shown again.

### 5. Audio Narration (Optional)
The final story can be narrated using OpenAI's TTS (`tts-1`, voice `nova`) and saved as an MP3. The file auto-plays on macOS, Windows, and Linux if a player is available.

---

## Research Basis

The prompting strategy is grounded in findings summarized by **Darcy Patterson** on what makes bedtime stories effective:

- **Carl-Johan Ehrlin** (*The Rabbit Who Wants to Fall Asleep*) — embedded sleep keywords and phonetically soft language as active sleep-induction tools
- **Lois Lowry** — the sound of words matters as much as their meaning; avoiding harsh consonants creates a calming sonic texture
- **Mem Fox** — the child-in-the-lap relationship; stories should end in a way that prompts a hug or "I love you" between child and reader
- **Language development research** — bedtime stories are a developmental opportunity; vocabulary, rhythm, sequencing, and nursery-rhyme repetition build language skills at age-appropriate milestones

---

## Project Structure

```
bedtime_story.py     # Main program
README.md            # This file
block_diagram.svg    # System architecture diagram
story_audio/         # Generated MP3 files (created on first audio request)
```

---

## Notes

- The OpenAI API key is read from the environment variable `OPENAI_API_KEY`. Do not hardcode it.
- The program uses the `openai` v0 SDK (`openai.ChatCompletion.create`). If you have v1+ installed, pin to `openai==0.28.0` or update the API calls accordingly.
- The judge runs at `temperature=0.0` for deterministic scoring. The storyteller runs at `temperature=0.25` for creative variety.
