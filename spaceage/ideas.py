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
        "prompt": "anime key visual, dramatic sky, detailed cel shading, studio quality",
        "effects": ["stars", "vignette"],
        "drone_hz": 73.4,
        "tags": ["#anime", "#mecha", "#animeart"],
    },
    "cosmic_horror": {
        "prompt": "cosmic horror, eerie fog, dim red emergency light, film still",
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
        "prompt": "grainy found footage, security camera still, night, realistic",
        "effects": ["scanlines", "grain", "glitch", "flicker"],
        "drone_hz": 49.0,
        "tags": ["#foundfootage", "#ufo", "#analoghorror"],
    },
    "space_opera": {
        "prompt": "epic space opera, vast scale, volumetric light, matte painting",
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
    "paperback80s": {
        "prompt": "1980s vintage sci-fi paperback cover art, airbrushed painting, grainy print",
        "effects": ["grain", "vignette", "flicker"],
        "drone_hz": 58.3,
        "tags": ["#80sscifi", "#scifiart", "#vintagescifi", "#retroscifi"],
    },
    "photoreal": {
        "prompt": "photorealistic, golden hour, dramatic lighting, sharp focus, highly detailed",
        "effects": ["vignette", "grain"],
        "drone_hz": 69.3,
        "tags": ["#photorealistic", "#digitalart", "#conceptart"],
    },
}

# Curated scenes, condensed from the account owner's own prompt collection.
# The model reads at most 75 CLIP tokens per prompt (scene + style + shot);
# run `python spaceage/ideas.py --check` after editing.
SCENES = [
    ("masked desert nomad warrior in ragged wrapped robes, beside a giant woolly beast of burden, dunes under two suns at sunset",
     ["photoreal", "paperback80s", "retro70s"]),
    ("masked desert nomad warrior in a detailed costume before a colossal Icelandic waterfall, steaming geysers, two suns setting",
     ["photoreal", "paperback80s"]),
    ("angular chrome space station module with small windows, sliding doors, hose pipes and wires, landed in an Icelandic desert",
     ["photoreal", "paperback80s", "retro70s"]),
    ("futuristic Bauhaus skyscrapers by Le Corbusier and Marcel Breuer, people on sidewalks, a giant waterfall behind the city",
     ["photoreal", "solarpunk", "synthwave"]),
    ("massive orbital space harbour with dozens of docked starships, interconnected modules above a lush green planet, swirling nebula",
     ["paperback80s", "space_opera", "retro70s"]),
    ("sleek silver space station of modules linked by tubes and walkways, inside a dark asteroid belt",
     ["paperback80s", "space_opera", "photoreal"]),
    ("derelict rusty space station slowly falling apart inside a dark nebula",
     ["cosmic_horror", "paperback80s", "found_footage"]),
    ("sleek starship escaping an asteroid base as huge titanium gates close behind it, glowing orange energy field, purple nebula",
     ["paperback80s", "space_opera", "anime"]),
    ("huge triangular starship with red and orange lights above a bluish grey planet, dark swirling nebula, bright distant star",
     ["paperback80s", "space_opera", "photoreal"]),
    ("massive crimson armored spaceship covered in antennas and satellite dishes, flying through a fiery nebula and asteroid fragments",
     ["paperback80s", "space_opera", "anime"]),
    ("towering retro rocket with pipes and spherical tanks landing on a cratered moon, golden light, distant glowing planet",
     ["retro70s", "paperback80s", "photoreal"]),
    ("futuristic battle cruiser flying through a stormy sky at dusk, fiery orange and purple clouds",
     ["photoreal", "space_opera", "anime"]),
    ("titanium exploration vessel with glowing engines passing a cratered exoplanet, distant galaxies",
     ["photoreal", "space_opera", "paperback80s"]),
    ("symmetrical silver space station with glowing red and blue thrusters and laser cannons, planets and icy asteroids behind",
     ["space_opera", "paperback80s", "photoreal"]),
    ("colossal titanium mothership like a space aircraft carrier, glass cockpit with pilots, cratered moon, asteroids",
     ["space_opera", "paperback80s", "photoreal"]),
    ("retro rocket blasting off from a crimson alien desert with jagged red rocks, orange flame trail, starry sky",
     ["paperback80s", "retro70s", "synthwave"]),
    ("young scientist in a futuristic control room facing a giant glowing AI core, holographic data streams",
     ["cyberpunk", "photoreal", "anime"]),
]

# Share of reels built from SCENES instead of random subject + style.
SCENE_SHARE = 0.6

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
    if rng.random() < SCENE_SHARE:
        subject, styles = rng.choice(SCENES)
        style_name = rng.choice(styles)
    else:
        subject = rng.choice(SUBJECTS)
        style_name = rng.choice(sorted(STYLES))
    style = STYLES[style_name]
    shots = rng.sample(SHOTS, 3)
    # Shot last: if a prompt is ever too long, the truncated part matters least.
    prompts = [f"{subject}, {style['prompt']}, {shot}" for shot in shots]

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


def all_prompts():
    """Every scene/subject + style + shot combination that make_idea can build."""
    pairs = [(s, st) for s, styles in SCENES for st in styles]
    pairs += [(s, st) for s in SUBJECTS for st in STYLES]
    return [f"{s}, {STYLES[st]['prompt']}, {shot}" for s, st in pairs for shot in SHOTS]


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["--check"]:
        # Needs the CLIP tokenizer: pip install open_clip_torch (or transformers).
        from transformers import CLIPTokenizer

        tok = CLIPTokenizer.from_pretrained("stabilityai/sd-turbo", subfolder="tokenizer")
        worst = max(all_prompts(), key=lambda p: len(tok(p).input_ids))
        n = len(tok(worst).input_ids)
        print(f"longest prompt: {n}/77 tokens\n{worst}")
        sys.exit(1 if n > 77 else 0)
    print(make_idea(int(sys.argv[1]) if len(sys.argv) > 1 else 42))
