import os
import json
import random
import subprocess
import sys
import threading
from datetime import datetime

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

# ====================== CONFIG ======================

# Phonetics guidance derived from Darcy Patterson / Ehrlin research:
# Minimize fricatives (f, v, th, s, z, sh, zh), affricates (ch, j),
# and plosives (b, p, t, d, k, g) — especially at stressed positions.
# Favor nasals (m, n), liquids (l, r), and soft vowels for a calming sonic texture.

PHONETIC_GUIDANCE = """
Phonetic guidelines (research-backed for sleep induction):
- MINIMIZE harsh consonants: fricatives (f, v, th, s, z, sh), affricates (ch, j), plosives (b, p, t, d, k, g)
- FAVOR soft sounds: nasals (m, n), liquids (l, r), long vowels (moon, glow, low, warm)
- You cannot avoid harsh consonants entirely, but minimize them especially in key calming phrases
- Example soft words: moon, lull, murmur, glow, meadow, mellow, velvet, golden, narrow, warm, nuzzle
- Example words to minimize: sharp, crack, stick, fast, buzz, scratch, jolt
"""

SLEEP_KEYWORDS = [
    "sleep now", "yawn", "drift gently", "rest quietly", "cozy", "warm",
    "slowly", "softly", "eyes heavy", "tucked in", "dreaming", "peaceful"
]

STORY_ARC = """
Story Arc (follow this structure exactly):
1. SETUP — Introduce the character in their warm, cozy, safe place. Establish comfort immediately.
2. GENTLE CHALLENGE — A small, soft problem arises. Never scary, threatening, or overly exciting.
3. RESOLUTION — The character solves it through kindness, creativity, or gentle perseverance.
4. WIND-DOWN — The world gets quieter. The character grows sleepy. Use sleep keywords naturally.
5. CLOSING MOMENT — End with warmth: a hug, "I love you", or a gentle loving gesture between characters.
   (Inspired by Mem Fox's child-in-the-lap relationship: the ending should make the child turn to the adult.)
"""

JUDGE_CRITERIA = """
You are a strict expert bedtime story judge. Evaluate the story against these research-backed criteria:

1. age_appropriateness (1-5): Vocabulary and themes suit the child's grade level. Sequencing is clear (beginning, middle, end). Cause-effect relationships are age-appropriate.
2. calmness (1-5): Minimal tension. No scary, stressful, or overly exciting content. The overall arc winds DOWN toward sleep.
3. phonetic_softness (1-5): Harsh consonants (fricatives, affricates, plosives) are minimized. Soft nasals, liquids, and long vowels dominate calming passages.
4. sleep_language (1-5): Sleep-inducing keywords appear naturally (sleep now, yawn, drift gently, cozy, warm, eyes heavy, etc.). Soothing repetition is present.
5. story_arc (1-5): Clear setup → gentle challenge → resolution → wind-down → warm closing moment.
6. language_development (1-5): Rich but appropriate vocabulary. Rhythm and sound patterns are present. Nursery-rhyme-like repetition for younger grades.
7. warm_ending (1-5): Story ends with a loving moment (hug, "I love you", gentle gesture) that invites child-adult connection.

Return ONLY valid JSON, no other text:
{
  "scores": {
    "age_appropriateness": <1-5>,
    "calmness": <1-5>,
    "phonetic_softness": <1-5>,
    "sleep_language": <1-5>,
    "story_arc": <1-5>,
    "language_development": <1-5>,
    "warm_ending": <1-5>
  },
  "issues": ["specific issue 1", "specific issue 2"],
  "pass": <true if ALL scores >= 4, else false>
}
"""

# ====================== CORE MODEL CALL ======================

def call_model(prompt: str, system: str = None, max_tokens: int = 2000, temperature: float = 0.2) -> str:
    if system is None:
        system = "You are a gentle bedtime storyteller for children aged 5-10."
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message["content"]


# ====================== AGE HELPERS ======================

def get_age_group(grade: str) -> str:
    grade_lower = str(grade).lower()
    if any(x in grade_lower for x in ["kindergarten", "k", "1", "2"]):
        return "5-7"
    return "8-10"


def get_age_specific_elements(grade: str) -> str:
    age_group = get_age_group(grade)
    if age_group == "5-7":
        return (
            "- Simple sequencing: clear beginning, middle, end\n"
            "- Gentle silly mistake or learning basic kindness/sharing\n"
            "- Nursery-rhyme-like repetition and rhythm\n"
            "- Very simple vocabulary; use sound words (murmur, hum, lull)\n"
            "- Short sentences with soft cadence"
        )
    return (
        "- Character has a sweet quirk and gentle inner thoughts\n"
        "- Light friendship or gentle perseverance theme\n"
        "- Slightly richer vocabulary with musical rhythm\n"
        "- Mild cause-effect reasoning the child can follow\n"
        "- Sentences can be longer but must still wind down to sleepiness"
    )


# ====================== STORY GENERATION ======================

def build_generation_prompt(genre: str, interests: str, user_input: str,
                             favorite_parts: list, grade: str) -> str:
    age_group = get_age_group(grade)
    memory = f"The child especially liked: {', '.join(favorite_parts)}\n" if favorite_parts else ""
    sleep_kw = ", ".join(SLEEP_KEYWORDS)

    return f"""Genre: {genre}
Child's interests: {interests}
Age group: {age_group} years old (Grade {grade})
{memory}
Write a calm, soothing bedtime story about: {user_input}

{STORY_ARC}

{PHONETIC_GUIDANCE}

Sleep Language:
- Weave these keywords in naturally throughout: {sleep_kw}
- Use gentle repetition of calming phrases (e.g. "and slowly, slowly..." or "soft and warm")
- Rhythm matters: read the story aloud in your mind; it should feel like a lullaby

Age-Specific Elements for Grade {grade}:
{get_age_specific_elements(grade)}

Length: 500-850 words
End with a warm, loving moment that makes the child want to hug the adult reading to them."""


def generate_draft(genre: str, interests: str, user_input: str,
                   favorite_parts: list, grade: str) -> str:
    prompt = build_generation_prompt(genre, interests, user_input, favorite_parts, grade)
    return call_model(prompt, max_tokens=1800, temperature=0.25)


# ====================== LLM JUDGE ======================

def judge_story(story: str, grade: str) -> dict:
    """
    Structured LLM judge. Returns scores, specific issues, and a pass/fail verdict.
    A story passes only when ALL criteria score >= 4.
    """
    age_group = get_age_group(grade)
    prompt = f"""Grade: {grade} | Age group: {age_group}

{JUDGE_CRITERIA}

Story to evaluate:
{story}"""

    raw = call_model(
        prompt,
        system="You are a strict, precise bedtime story quality judge. Return only valid JSON.",
        max_tokens=500,
        temperature=0.0
    )

    # Strip markdown fences if model wraps output
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # Fallback: assume fail so we trigger a revision rather than silently passing bad output
        return {
            "scores": {},
            "issues": ["Judge output could not be parsed — treating as failed review."],
            "pass": False
        }


def revise_story(story: str, issues: list, grade: str) -> str:
    """
    Targeted revision pass. Feeds specific judge issues back into the model.
    """
    issue_list = "\n".join(f"- {issue}" for issue in issues)
    age_group = get_age_group(grade)

    prompt = f"""You are revising a bedtime story for grade {grade} ({age_group} years old).

A quality judge found these specific problems:
{issue_list}

Revision requirements:
{PHONETIC_GUIDANCE}
- Fix every issue listed above
- Preserve the story arc: setup → gentle challenge → resolution → wind-down → warm ending
- Keep sleep keywords and soothing repetition
- Do NOT make the story more exciting or tense
- Return only the revised story, no commentary

Original story:
{story}"""

    return call_model(prompt, max_tokens=1900, temperature=0.15)


def run_judge_loop(draft: str, grade: str, max_attempts: int = 3) -> tuple[str, dict]:
    """
    Judge loop: evaluate → revise if failed → repeat up to max_attempts.
    Returns (final_story, final_verdict).
    """
    story = draft
    verdict = {}

    for attempt in range(1, max_attempts + 1):
        print(f"   ⚖️  Judge review — attempt {attempt}/{max_attempts}...")
        verdict = judge_story(story, grade)

        scores = verdict.get("scores", {})
        if scores:
            score_display = " | ".join(f"{k[:4]}: {v}" for k, v in scores.items())
            print(f"   📊 {score_display}")

        if verdict.get("pass"):
            print(f"   ✅ Story passed on attempt {attempt}")
            break

        issues = verdict.get("issues", [])
        if issues:
            print(f"   🔧 Revising — issues found: {len(issues)}")
            for issue in issues:
                print(f"      • {issue}")

        if attempt < max_attempts:
            story = revise_story(story, issues, grade)
        else:
            print("   ⚠️  Max revision attempts reached — using best version")

    return story, verdict


# ====================== FULL STORY PIPELINE ======================

def generate_bedtime_story(genre: str, interests: str, user_input: str,
                            favorite_parts: list, grade: str) -> tuple:
    print("🌙 Writing initial story draft...")
    draft = generate_draft(genre, interests, user_input, favorite_parts, grade)

    print("🔍 Running LLM judge loop...")
    final_story, verdict = run_judge_loop(draft, grade)

    title = generate_story_title(final_story)
    return title, final_story, verdict


def generate_story_title(story: str) -> str:
    try:
        prompt = f"Give this bedtime story a short, beautiful title (max 6 words):\n\n{story[:500]}"
        return call_model(prompt, max_tokens=40, temperature=0.3).strip()
    except Exception:
        return "A Gentle Bedtime Story"


# ====================== CLASSIC RETELLING ======================

def get_bedtime_classic(grade: str) -> tuple:
    classics = [
        "Goodnight Moon", "The Very Hungry Caterpillar", "Guess How Much I Love You",
        "Winnie the Pooh", "The Rainbow Fish", "Little Bear"
    ]
    selected = random.choice(classics)
    print(f"\n🌙 Retelling {selected}...")

    prompt = f"""Retell "{selected}" as a calm, peaceful bedtime story for grade {grade}.

{STORY_ARC}
{PHONETIC_GUIDANCE}

Use minimal tension, soft language, gentle repetition, sleep keywords, and a warm loving ending."""

    draft = call_model(prompt, max_tokens=1800, temperature=0.15)

    print("🔍 Running LLM judge loop...")
    final_story, verdict = run_judge_loop(draft, grade)
    title = generate_story_title(final_story)
    return f"Classic: {selected}", final_story, verdict


# ====================== USER FEEDBACK REVISION ======================

def revise_story_with_feedback(story: str, feedback: str, grade: str) -> tuple:
    """
    Let the user request changes to the current story.
    Re-runs judge loop after revision.
    """
    print("\n✏️  Revising story based on your feedback...")
    prompt = f"""Revise this bedtime story based on this request: "{feedback}"

Important: Keep everything gentle, calming, and age-appropriate for grade {grade}.
Preserve the story arc and warm ending.
Return only the revised story.

Original story:
{story}"""

    revised = call_model(prompt, max_tokens=1900, temperature=0.2)

    print("🔍 Re-running judge on revised story...")
    final_story, verdict = run_judge_loop(revised, grade)
    title = generate_story_title(final_story)
    return title, final_story, verdict


# ====================== FAVORITES ======================

def load_favorites() -> list:
    try:
        if os.path.exists("favorites.json"):
            with open("favorites.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_favorites(favorites: list) -> None:
    try:
        with open("favorites.json", "w", encoding="utf-8") as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ====================== AUDIO ======================

def read_story_aloud(story_text: str, story_number: int) -> None:
    try:
        print("\n🎤 Generating gentle narration...")
        response = openai.Audio.create(model="tts-1", voice="nova", input=story_text)

        os.makedirs("story_audio", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = f"story_audio/story_{story_number}_{ts}.mp3"

        with open(audio_file, "wb") as f:
            f.write(response.content)

        try:
            if os.name == "nt":
                subprocess.Popen(["start", audio_file], shell=True)
            elif "darwin" in sys.platform:
                subprocess.Popen(["open", audio_file])
            else:
                subprocess.Popen(["xdg-open", audio_file])
            print("▶️  Playing bedtime story...")
        except Exception:
            print(f"💡 Audio saved: {audio_file}")
    except Exception as e:
        print(f"⚠️  Could not generate audio: {e}")


# ====================== INPUT WITH TIMEOUT ======================

def input_with_timeout(prompt: str, timeout: int = 600) -> str:
    print(prompt)
    result = []

    def get_input():
        result.append(input().strip())

    thread = threading.Thread(target=get_input)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        print("\n\n⏰ No response for 10 minutes. Sweet dreams! 🌙")
        sys.exit(0)

    return result[0] if result else ""


# ====================== MAIN ======================

def main():
    print("🌙 Welcome to the Bedtime Story Generator 🌙\n")
    print("Research-backed stories • LLM judge loop • Age-appropriate development\n")

    grade = input("What grade is the child in? (e.g. Kindergarten, 1, 2, 3, 4): ").strip() or "2"
    genre = input("Preferred gentle genre? (e.g. animals, stars, forest, ocean, dreams): ").strip()
    interests = input("What is the child interested in? ").strip()

    favorites = load_favorites()
    favorite_parts = []
    story_counter = 1

    while True:
        if favorite_parts:
            print(f"\nI remember you liked: {', '.join(favorite_parts)}\n")

        print("\nWhat would you like tonight?")
        print("1. New original bedtime story")
        print("2. Bedtime classic")
        print("3. My Favorites")
        mode = input("Choose (1, 2 or 3): ").strip()

        verdict = {}

        if mode == "3":
            if not favorites:
                print("You don't have any saved favorites yet.")
                continue
            print("\n📚 Your Favorite Stories:")
            for i, fav in enumerate(favorites, 1):
                print(f"   {i}. {fav['title']}")
            try:
                sel = int(input("\nChoose story number: "))
                title = favorites[sel - 1]["title"]
                story = favorites[sel - 1]["story"]
            except (ValueError, IndexError):
                print("Invalid choice.")
                continue

        elif mode == "2":
            title, story, verdict = get_bedtime_classic(grade)

        else:
            user_input = input("\nWhat kind of bedtime story would you like? ").strip()
            print("\n🌙 Creating your special story...\n")
            title, story, verdict = generate_bedtime_story(
                genre, interests, user_input, favorite_parts, grade
            )

        print("=" * 85)
        print(f"🌙 {title}\n")
        print(story)
        print("=" * 85)

        # Show judge scores if available
        if verdict.get("scores"):
            print("\n📊 Story Quality Scores:")
            for criterion, score in verdict["scores"].items():
                bar = "█" * score + "░" * (5 - score)
                print(f"   {criterion:<22} {bar} {score}/5")

        # User feedback → live revision of current story
        feedback = input("\nAnything you'd like changed in this story? (press Enter to keep): ").strip()
        if feedback:
            title, story, verdict = revise_story_with_feedback(story, feedback, grade)
            print("\n" + "=" * 85)
            print(f"🌙 {title} (revised)\n")
            print(story)
            print("=" * 85)

        # Save to favorites
        liked = input("\nDid you like this story? (yes/no): ").strip().lower()
        if liked in ["yes", "y", "yeah"]:
            favorites.append({"title": title, "story": story})
            save_favorites(favorites)
            print("❤️  Saved to your Favorites!")

        # Remember favorite parts for next story
        fav_part = input("\nWhat was your favorite part? ").strip()
        if fav_part and fav_part.lower() not in ["nothing", "none", ""]:
            favorite_parts.append(fav_part)

        # Audio option
        choice = input("\nWould you like to:\n1. Just read the story\n2. Listen to the story\nChoose (1 or 2): ").strip()
        if choice == "2":
            read_story_aloud(story, story_counter)

        story_counter += 1

        again = input_with_timeout("\nWould you like another bedtime story? (yes/no) ", timeout=600)
        if again.lower() not in ["yes", "y", ""]:
            print("\nGoodnight and sweet dreams! 🌙")
            break


if __name__ == "__main__":
    main()
