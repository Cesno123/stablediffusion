"""Random sci-fi reel ideas: style, subject, prompt, caption and hashtags.

No external service is used. Every idea is a combination of the lists below,
picked with a seeded RNG so the same seed always yields the same idea.
Add your own entries to the lists to widen the variety.
"""

import random
from dataclasses import dataclass, field

# Each style sets the prompt look, the post-processing effects and the sound.
STYLES = {
    "cyberpunk": {
        "prompt": "neon-lit cyberpunk, rain, magenta and cyan lights, cinematic, blade runner mood",
        "effects": ["chroma", "scanlines", "grain", "vignette"],
        "drone_hz": 55.0,
        "tags": ["#cyberpunk", "#neon", "#cyberpunkart"],
    },
    "retro70s": {
        "prompt": "1970s retro-futurism, vintage sci-fi paperback cover art, airbrush, warm orange and teal",
        "effects": ["grain", "vignette", "flicker"],
        "drone_hz": 65.4,
        "tags": ["#retrofuturism", "#70sscifi", "#vintagescifi"],
    },
    "anime": {
        "prompt": "anime key visual, mecha, dramatic sky, detailed cel shading, studio quality",
        "effects": ["stars", "vignette"],
        "drone_hz": 73.4,
        "tags": ["#anime", "#mecha", "#animeart"],
    },
    "cosmic_horror": {
        "prompt": "cosmic horror, derelict spaceship interior, eerie fog, dim red emergency light, film still",
        "effects": ["grain", "flicker", "glitch", "vignette"],
        "drone_hz": 41.2,
        "tags": ["#cosmichorror", "#scifihorror", "#darkart"],
    },
    "solarpunk": {
        "prompt": "solarpunk utopia, lush vertical gardens, white architecture, golden hour, optimistic, highly detailed",
        "effects": ["vignette", "grain"],
        "drone_hz": 87.3,
        "tags": ["#solarpunk", "#utopia", "#futurecity"],
    },
    "found_footage": {
        "prompt": "grainy found footage, security camera still, strange object in the sky, night, realistic",
        "effects": ["scanlines", "grain", "glitch", "flicker"],
        "drone_hz": 49.0,
        "tags": ["#foundfootage", "#ufo", "#analoghorror"],
    },
    "space_opera": {
        "prompt": "epic space opera, colossal starship fleet above a gas giant, volumetric light, matte painting",
        "effects": ["stars", "vignette", "grain"],
        "drone_hz": 61.7,
        "tags": ["#spaceopera", "#spaceart", "#starship"],
    },
    "synthwave": {
        "prompt": "synthwave, outrun, retro grid, giant sunset, chrome, 80s aesthetic, vaporwave colors",
        "effects": ["scanlines", "chroma", "vignette"],
        "drone_hz": 82.4,
        "tags": ["#synthwave", "#outrun", "#retrowave"],
    },
}

SUBJECTS = [
    "a lone astronaut",
    "an abandoned space station",
    "a giant alien monolith",
    "a floating city",
    "an android looking at the stars",
    "a starship leaving orbit",
    "an alien jungle planet",
    "a mining colony on an asteroid",
    "a robot in a desert",
    "a portal opening in the sky",
    "a crashed spaceship",
    "a mega-city at night",
]

# Three shots per reel; they get cross-faded into each other.
SHOTS = [
    "wide establishing shot",
    "medium shot",
    "close-up detail",
    "low angle shot",
    "aerial view",
]

HOOKS = [
    "Year {year}. {subject_cap}.",
    "They told us not to look up.",
    "Signal lost at {year}.",
    "The last transmission from {subject}.",
    "Somewhere in sector {sector}...",
    "Would you go?",
]

BASE_TAGS = ["#scifi", "#aiart", "#sciencefiction", "#futuristic", "#spaceage42"]

NEGATIVE = "text, watermark, logo, signature, blurry, deformed, lowres"


@dataclass
class Idea:
    style: str
    subject: str
    prompts: list
    negative: str
    effects: list
    drone_hz: float
    hook: str
    caption: str
    tags: list = field(default_factory=list)


def make_idea(seed: int) -> Idea:
    rng = random.Random(seed)
    style_name = rng.choice(sorted(STYLES))
    style = STYLES[style_name]
    subject = rng.choice(SUBJECTS)
    shots = rng.sample(SHOTS, 3)
    prompts = [f"{subject}, {shot}, {style['prompt']}" for shot in shots]

    hook = rng.choice(HOOKS).format(
        year=rng.randint(2140, 9999),
        sector=rng.randint(1, 99),
        subject=subject,
        subject_cap=subject[0].upper() + subject[1:],
    )
    tags = BASE_TAGS + style["tags"]
    caption = f"{hook}\n\nStyle: {style_name.replace('_', ' ')}\n\n" + " ".join(tags)

    return Idea(
        style=style_name,
        subject=subject,
        prompts=prompts,
        negative=NEGATIVE,
        effects=list(style["effects"]),
        drone_hz=style["drone_hz"],
        hook=hook,
        caption=caption,
        tags=tags,
    )


if __name__ == "__main__":
    import sys

    print(make_idea(int(sys.argv[1]) if len(sys.argv) > 1 else 42))
