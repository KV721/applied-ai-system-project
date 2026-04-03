# 🎧 Model Card: Music Recommender Simulation

---

## 1. Model Name

**MoodQ**

A content-based music recommender that scores songs against a user's taste profile and explains every recommendation in plain language.

---

## 2. Goal / Task

VibeMatch tries to answer one question: given what a user tells us they like, which songs from our catalog are the closest match?

It suggests songs based on four things the user tells us: their preferred genre, their current mood, how energetic they want the music to feel, and whether they prefer acoustic or produced sounds. It does not learn from behavior over time. Every recommendation is based purely on how well a song's attributes match the user's stated preferences.

---

## 3. Algorithm Summary

Think of it like a scorecard. Every song gets graded on four questions:

- **Does the genre match?** If yes, the song gets 35 points out of 100. If not, it gets zero. No partial credit.
- **Does the mood match?** Same idea — 30 points if it matches exactly, zero if not.
- **How close is the energy?** Songs that feel about as intense as the user wants score up to 20 points. The further away, the fewer points. A gym-level intense song scores low for someone who wants background study music.
- **Does the tone feel right?** We infer a target positivity level from the user's mood. Happy users get points for upbeat-sounding songs. Melancholic users get points for lower-valence songs. Worth up to 10 points.
- **Acoustic or produced?** If the user likes acoustic sounds, songs with more natural texture score up to 5 extra points. Electronic or heavily produced songs score up to 5 points for users who prefer that texture.

All five scores are added together. The songs are then sorted from highest to lowest, and the top five are returned with a sentence explaining why each one ranked where it did.

---

## 4. Data Used

The catalog has **28 songs** stored in `data/songs.csv`.

Each song has nine attributes: title, artist, genre, mood, energy (0–1), tempo in BPM, valence (0–1 positivity), danceability (0–1), and acousticness (0–1).

**Genres represented:** lofi, pop, folk, hip-hop, r&b, classical, country, metal, rock, ambient, jazz, synthwave, indie pop, blues, reggae, drum and bass, indie rock, funk, alternative — 19 genres total.

**Moods represented:** chill, intense, dark, peaceful, happy, nostalgic, energetic, romantic, melancholic, uplifting, relaxed, moody, focused, playful — 14 moods total.

The original starter file had 10 songs. We added 18 more to fill in missing genres and moods. Even so, 11 out of 19 genres still have only one song. That is a real limitation.

**What's missing:** No songs with energy below 0.18. No Latin, classical Indian, or world music genres. Danceability and tempo are in the data but not used in scoring. The catalog reflects a narrow slice of musical taste — mostly Western genres, no lyrics-based features, no artist popularity data.

---

## 5. Strengths

The system works best when the user's preferences match a well-represented part of the catalog.

- **Clear, explainable results.** Every recommendation comes with a plain-English reason. You always know why a song was suggested.
- **Lofi and chill users get solid results.** Three lofi songs and three chill songs exist, so there are real choices to rank rather than a single forced pick.
- **Standard profiles work as expected.** A pop/happy user reliably gets upbeat pop songs at the top. A rock/intense user reliably gets Storm Runner first. The scoring logic is transparent enough that results are predictable and debuggable.
- **The explanation catches mistakes.** Because the "why" is always printed, it's easy to spot when something looks off — you can immediately see whether genre or mood drove a result.

---

## 6. Limitations and Bias

The most significant problem is the **single-song genre bubble**. Eleven out of nineteen genres have exactly one song. When a user picks one of these genres — blues, reggae, funk, indie rock, drum and bass — that lone song gets a guaranteed 35 point genre bonus no other song can match. It almost always comes out #1, even if its mood and energy are a poor fit. The system looks confident, but that confidence comes from having no competition, not from being a good match.

A second problem is that **the energy gap never disqualifies a song**. Even if a song's energy is completely wrong, say 0.95 when the user wants 0.15, it still gets a small positive score. The system has no way to say "nothing in this catalog fits you well right now."

**Two features are loaded but ignored.** Danceability and tempo are in every song's data but are never used in scoring. A user who wants to dance and a user who wants to study get identical recommendations if their genre, mood, and energy match.

The **mood label system is fragile**. Moods like "melancholic" and "dark" feel similar but are treated as completely different. A user who types a mood we don't recognize, like "bittersweet" or "anxious", silently gets treated the same as a "chill" user, with no warning.

Finally, **the catalog is uneven by energy level**. Seven songs cluster in the 0.30 - 0.45 energy range, while zero songs exist below 0.18. Users who want very quiet, minimal music have no good options.

---

## 7. Evaluation Process

We tested seven user profiles in total, three normal and four designed to break the system.

**Normal profiles:**
- *High-Energy Pop* — worked well. Sunrise City was a clear winner.
- *Chill Lofi* — worked well, but Library Rain and Midnight Coding scored almost identically. No meaningful tiebreaker.
- *Deep Intense Rock* — exposed the single-song bubble. Storm Runner scored 0.985. Everything else dropped to 0.62 or below.

**Edge case profiles:**
- *Conflicting preferences* (melancholic mood + high energy) — a slow, sad song ranked #1 because it shared the genre label, even though a fast intense song would have matched the energy much better. Genre won an argument it shouldn't have.
- *Ghost genre* (k-pop, not in catalog) — genre bonus was zero for every song. All results clustered together with no real winner. The system had no fallback.
- *Extremes* (ambient + peaceful + energy 0.15) — the peaceful mood had no catalog matches, so mood points were never awarded. The genre-matched song (Spacewalk Thoughts) beat more emotionally fitting songs just because of its genre tag.
- *Contradictory acoustic* (metal + likes acoustic) — metal songs have almost no acoustic texture, so the acoustic preference silently penalized every result. The system didn't flag the contradiction.

**Weight shift experiment:** we doubled the energy weight and halved the genre weight. Rooftop Lights (indie pop) jumped above Gym Hero (pop) for the Happy Pop profile because it had closer energy, a cross-genre song beat an in-genre song. This showed that the default weights make genre matter almost twice as much as how a song actually sounds.

---

## 8. Intended Use and Non-Intended Use

**This system is designed for:**
- Classroom exploration of how content-based recommenders work
- Understanding how feature weights affect ranking
- Demonstrating the difference between collaborative filtering and content-based filtering
- Learning projects where transparency matters more than accuracy

**This system should NOT be used for:**
- Real music discovery for actual users, the catalog is too small and biased
- Making decisions that affect artists or listeners in a real product
- Any setting where a single-song genre bubble would consistently surface one song as a "recommendation"
- Users who expect the system to learn from their listening behavior over time, it cannot do that

---

## 9. Ideas for Improvement

1. **Use danceability and tempo in scoring.** These two features are already in the data. Adding danceability would meaningfully separate a "party" user from a "study" user who both want the same genre and mood. Normalizing tempo to a 0–1 range and including it would help distinguish a 60 BPM ambient track from a 174 BPM drum and bass track for users who care about pace.

2. **Soft-match genres instead of binary.** Right now, `indie pop` and `pop` are treated as completely different, zero shared credit. A similarity map (e.g., lofi ≈ ambient ≈ jazz for low-energy texture; pop ≈ indie pop ≈ synthwave for mid-energy produced sound) would let the system surface near-genre matches instead of falling off a cliff when an exact genre match doesn't exist or has only one song.

3. **Add a diversity filter to the ranking step.** Right now the system sorts by score and takes the top five. If five lofi songs score similarly, all five appear. A real recommender would enforce variety — for example, no more than two songs from the same genre or artist in the top five — so the results feel like a playlist, not a pile of clones.

---

## 10. Personal Reflection

The biggest learning moment was realizing that a recommendation is not the same thing as a good match. Early on, the system was producing results that looked reasonable, a song came out #1, a score was printed, a reason was displayed, and it felt like the system was working. Then we ran the adversarial profiles. A slow, sad song ranked above fast intense ones because it shared a genre label. A genre that didn't exist in the catalog caused all scores to cluster with no real winner. A song with almost no acoustic texture still "won" for a user who said they liked acoustic music. The system was always producing output, but output is not the same as accuracy. That gap, between a system that runs and a system that works, was the clearest thing this project taught me.

Using AI tools during this project helped most in the exploratory phases. When we were thinking through which features to weight and why, having a structured breakdown of Spotify's actual approach gave the decisions a real-world anchor rather than making them feel arbitrary. The bias audit, where we mapped which genres had only one song and which moods had no catalog matches, would have taken much longer to notice manually. But I did need to double-check the weight math when the experiment changed the coefficients. The tool confirmed the weights summed to 1.0, but I verified it myself before trusting the output, because a scoring function that doesn't sum to 1.0 silently produces scores that are incomparable across runs. That kind of numerical correctness is easy to miss when moving fast.

If I extended this project, the first thing I'd try is replacing the binary genre match with a soft similarity score. Genre labels are too blunt, "indie pop" and "pop" are almost the same thing to a listener, but the system treats them as completely unrelated. Building a small genre graph where related genres share partial credit would immediately improve results for users whose exact genre has few catalog matches. After that, I'd add a minimum score threshold so the system can say "nothing in this catalog is a strong match" instead of always confidently returning five results. Honest uncertainty is more useful than false confidence, and right now the system has no way to express it.
