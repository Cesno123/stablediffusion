"""Cover-art scenes for the GPU pipeline (FLUX images + LTX video on Kaggle).

Modelled on 1970s/80s sci-fi paperback covers: one clear hero object,
plausible hard-surface design, bold colour contrast, painted look.
FLUX reads long prompts (T5, 256 tokens here), so these can be descriptive.
Each entry: (scene, motion) – motion describes what moves in the video.
"""

import random

STYLE = (
    "Vintage 1970s-1980s science fiction illustration painting, airbrushed gouache "
    "on board, meticulous hard-surface spaceship design with panel lines, hull markings "
    "and coherent symmetrical engineering, single clear subject, dramatic scale, bold "
    "complementary colours, subtle paint texture, artwork only without any book title."
)

SCENES = [
    ("A tall retro rocket with three swept fins and riveted silver hull, two gold bands, "
     "standing on a cratered lunar plain under a huge full moon and golden stars, "
     "etched black-and-gold illustration look",
     "stars twinkle, thin dust drifts across the ground, the camera slowly rises along the rocket"),
    ("A long blue modular cargo starship with a large spherical command module at the front, "
     "white hull plates, orange stripes and cable rigging, drifting past two dark eclipsed "
     "planets with glowing rims, a tiny repair drone nearby",
     "the starship glides slowly to the right, the planet rims shimmer, the drone drifts"),
    ("A boxy white dropship with folded wings and the hull number 0-330 hovering low over a "
     "red desert, a cable hanging down to two astronauts in orange suits, red dust storm sky",
     "the dropship hovers and sways gently, dust swirls, the cable sways"),
    ("A flying saucer carrying a glass dome with a green forest inside, glowing underside "
     "engine, floating above jagged icy mountain peaks and a sea of clouds, blue sky with stars",
     "the saucer floats and slowly rotates, clouds flow between the peaks, the engine pulses"),
    ("A sleek red and white starfighter with twin engine pods and bright white exhaust "
     "flames, racing through an orange nebula toward a purple star cluster",
     "the starfighter surges forward, exhaust flames flicker, the nebula streams past"),
    ("A huge domed city hovering above a red alien plain, a streamlined hover car and small "
     "flying craft below, glowing yellow roads, dark night sky",
     "small craft fly past, lights in the domed city flicker, the camera drifts forward"),
    ("A battered white armoured battleship with antenna arrays rising over a desert world, "
     "a giant ringed orange gas giant and a dark moon behind, low golden sunlight",
     "the battleship climbs slowly, sunlight glints off the hull, the rings shimmer"),
    ("A colossal black pyramid-shaped alien craft with glowing red circuit patterns "
     "hovering point-down above an ancient stone pyramid in the desert, blue evening sky",
     "the alien pyramid slowly rotates, the red circuits pulse with light"),
    ("Two cylindrical landing capsules rising on orange rocket flames from a cratered rocky "
     "moon, a huge pockmarked planet behind, dense starfield",
     "the capsules ascend on bright flames, sparks and dust spray from the ground"),
    ("A long white starship with the hull number 702, rows of windows and a cluster of "
     "boxy engine pods at the stern, sailing through a purple nebula past a bright star",
     "the starship glides slowly across the frame, the bright star flares"),
    ("A copper-domed tower station on a single tall pylon rising out of a colossal "
     "waterfall at the edge of an ocean, mist and spray, another plume in the distance",
     "water thunders down the falls, mist rises and drifts, the camera slowly pulls back"),
    ("A gigantic green camouflage carrier ship with orange stripes and the number 2, "
     "blocky hangar decks and antennas, floating in a red and orange star-filled sky",
     "the carrier drifts forward, small lights blink along the hangar decks"),
    ("A dark streamlined warship shaped like a submarine with a tall bridge tower, "
     "red trim lines, diving through a swirling turquoise energy vortex",
     "the warship dives forward, the turquoise energy streaks swirl around it"),
    ("An orbital space harbour ring with dozens of docked freighters, cranes and lit "
     "hangar bays, above a lush green planet, a swirling nebula behind",
     "a freighter undocks and moves away, harbour lights blink, the ring turns slowly"),
    ("A massive titanium mothership like an aircraft carrier for starfighters, glass "
     "bridge with tiny pilots visible, a cratered moon and asteroids, yellow-white sun",
     "small fighters launch from the deck, the sun flares, asteroids drift"),
]

HOOKS = [
    "Cover art from a book that was never written.",
    "Found on a paperback from 2187.",
    "Which mission would you join?",
    "They built it to last a thousand years.",
    "Departure in T-minus 10.",
    "Retro future, rendered today.",
]

TAGS = ["#scifi", "#scifiart", "#retrofuturism", "#80sscifi", "#vintagescifi",
        "#spaceart", "#conceptart", "#aiart", "#spaceage42"]

NEGATIVE_VIDEO = "worst quality, inconsistent motion, blurry, jittery, distorted, morphing, text"


def make_job(seed: int, count: int, videos: int) -> dict:
    """Pick `count` different scenes; the first `videos` also get a video clip."""
    rng = random.Random(seed)
    picks = rng.sample(SCENES, min(count, len(SCENES)))
    items = []
    for i, (scene, motion) in enumerate(picks):
        items.append({
            "seed": seed * 10 + i,
            "prompt": f"{scene}. {STYLE}",
            "motion": f"{scene}. {motion}. Cinematic, smooth slow motion, painted sci-fi cover art.",
            "video": i < videos,
            "caption": f"{rng.choice(HOOKS)}\n\n" + " ".join(TAGS),
        })
    return {"seed": seed, "items": items, "negative_video": NEGATIVE_VIDEO}
