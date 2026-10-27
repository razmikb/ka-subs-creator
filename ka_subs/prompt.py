"""The instructions Gemini gets with each audio part (PLAN.md §3.2), with the Khan Academy
subtitle guidelines added: support.khanacademy.org/hc/en-us/articles/226430248.

The same text is used for the API and for pasting into AI Studio by hand.
"""

PROMPT = """This is the audio of a Georgian educational video (Khan Academy). Write a word-for-word transcript in Georgian.

Rules:
- Transcribe EVERYTHING that is said, from the first second to the last. Do not skip, shorten or summarise any part, even if it seems repetitive or unimportant.
- Leave out filler sounds (like "ამმ", "ეეე"), false starts and side remarks that are not part of the lesson. If the speaker breaks off and restarts a sentence, mark the break with a double dash (--).
- Numbers: write zero to nine as words (ნული, ერთი ... ცხრა). Write 10 and above as digits (16, 81, 216), with the Georgian ending after a hyphen (16-ს, 81-ის). In a list that also has numbers of 10 or more, write all of them as digits (1, 2, 3, 10). Write 1000 without a comma, and 10 000 / 100 000 with a space.
- Maths: write equations and expressions as the words that are SPOKEN, not as symbols ("ერთს პლუს ერთი უდრის ორს", not "1+1=2"). Write powers, roots, functions and decimals the way the speaker says them. A fraction said as "x over 5" may be written with a slash (x/5); write units in full words (გრამი, მეტრი).
- One sentence per line.
- No timestamps, no speaker names, no headings, no translation, no comments of your own.
- Plain text only, no markdown.
"""
