"""Random sci-fi image prompts: subject x style x palette x composition x mood.

Every call draws a fresh combination, so the owner does not know the image in
advance. Extend the lists to widen the variety; the counts multiply.
"""

import random

SUBJECTS = [
    "a colossal mothership hovering over a desert city",
    "a lone astronaut walking through a crystal canyon",
    "an abandoned space station overgrown with alien plants",
    "a flying saucer above a sleeping small town at night",
    "a Mars colony of domes, greenhouses and rovers",
    "a ringworld seen from its inner surface with oceans and clouds",
    "a Dyson sphere under construction around a blue star",
    "two fleets of starships clashing above a gas giant",
    "a giant robot standing guard in a ruined city",
    "an android sitting alone in a rain-soaked noodle bar",
    "a rocket launching from a coastal launch pad at dawn",
    "an underwater research base beneath the ice of a frozen moon",
    "a space elevator rising from a tropical island into orbit",
    "a starship escaping the glowing edge of a black hole",
    "a mecha pilot next to a giant robot in a hangar",
    "a generation ship with thousands of lit windows approaching an ocean planet",
    "a floating city of spires resting on huge hover pods",
    "an alien jungle with towering bioluminescent mushrooms and a small rover",
    "a derelict freighter drifting through an asteroid field",
    "a crashed spaceship half buried in snow under three moons",
    "a spaceport with ships lifting off between skyscrapers",
    "a cathedral-like battleship drifting through a dark nebula",
    "a mining ship anchored to a glowing asteroid with cranes and sparks",
    "a desert outpost of domes and radar dishes under two setting suns",
    "a sci-fi soldier in heavy armor standing in a snowstorm",
    "an orbital harbour ring with docked freighters above a green planet",
    "a broken Dyson sphere shell with oceans on its inner surface",
    "a scout ship flying low over an alien ocean with giant waves",
    "a cyborg explorer looking at an ancient alien monolith",
    "a tram of glass capsules gliding through a futuristic garden city",
    "a lighthouse-like beacon station at the edge of a galaxy",
    "a giant spherical floating city surrounded by balloons and airships",
    "a portal opening in the sky above mountain peaks",
    "a convoy of hover trucks crossing a red Martian plain",
    "an observatory on an airless moon with Earth rising behind it",
    "a sleek starfighter racing through a canyon on an alien world",
    "a space whale swimming past a planet with rings",
    "a retro rocket standing on a cratered moon under a huge full moon",
    "a futuristic monastery built into a cliff on an alien planet",
    "a black pyramid-shaped alien craft hovering above an ancient desert",
]

STYLES = [
    "1950s pulp magazine cover painting, bold retro rocket age",
    "1970s British science fiction paperback painting, airbrushed gouache",
    "1980s Japanese anime cel art, hand-painted",
    "Soviet space program propaganda poster, bold flat colors",
    "vintage 1970s NASA space colony concept painting",
    "French ligne claire comic art, clean ink lines, flat colors",
    "retro technical blueprint, white lines on blue paper",
    "Japanese ukiyo-e woodblock print",
    "1960s space age travel poster, screen print",
    "art deco poster with geometric shapes and gold accents",
    "cinematic film still, photorealistic, volumetric light",
    "hyper-detailed 3D render, ray tracing, studio lighting",
    "neon cyberpunk night scene, rain reflections",
    "synthwave vaporwave aesthetic, neon glow, retro grid",
    "isometric miniature diorama, tilt-shift photography",
    "16-bit pixel art",
    "minimalist vector poster, flat shapes, limited palette",
    "loose watercolor and ink sketch",
    "dark gothic science fiction oil painting",
    "detailed matte painting, epic scale",
    "claymation stop-motion still, handmade clay models",
    "stained glass window art",
    "linocut print, bold black lines, two colors",
    "Polaroid photograph, faded colors, light leaks",
    "vintage Kodachrome photograph from 1962",
    "comic book splash page, dynamic inking, halftone dots",
    "low-poly 3D art, faceted shapes",
    "impressionist oil painting, visible brush strokes",
    "papercut layered art, depth and shadows",
    "concept art for a video game, painterly, high detail",
]

PALETTES = [
    "orange and teal", "crimson and black", "pastel pink and lavender",
    "icy blue and white", "golden hour warm tones", "emerald green and copper",
    "monochrome blue", "black and gold", "sunset purple and orange",
    "muted earth tones", "neon magenta and electric blue", "sepia and cream",
    "deep red and cyan", "silver and midnight blue", "acid green and violet",
    "soft dawn yellow and grey", "rust and turquoise", "high-contrast black and white",
    "candy colors", "dusty desert beige and sky blue",
]

COMPOSITIONS = [
    "dramatic low angle", "wide establishing shot", "close-up detail",
    "aerial view from above", "symmetrical centered composition",
    "diagonal dynamic composition", "silhouette against a bright sky",
    "tiny figure for scale against something enormous", "seen through a window",
    "over-the-shoulder view", "panoramic vista", "fisheye perspective",
    "rule of thirds with lots of negative space", "cutaway view", "reflection in water",
]

MOODS = [
    "peaceful and quiet", "epic and heroic", "eerie and mysterious",
    "melancholic", "hopeful", "tense and dramatic", "dreamlike",
    "lonely", "joyful and adventurous", "ominous", "nostalgic", "awe-inspiring",
]

SUFFIX = "no text, no lettering, no watermark, no signature"


def make_prompt(rng=None):
    rng = rng or random.Random()
    parts = {
        "subject": rng.choice(SUBJECTS),
        "style": rng.choice(STYLES),
        "palette": rng.choice(PALETTES),
        "composition": rng.choice(COMPOSITIONS),
        "mood": rng.choice(MOODS),
    }
    prompt = (f"{parts['subject']}, {parts['composition']}, {parts['mood']} mood, "
              f"{parts['palette']} color palette, {parts['style']}, {SUFFIX}")
    return prompt, parts


def combinations():
    n = 1
    for lst in (SUBJECTS, STYLES, PALETTES, COMPOSITIONS, MOODS):
        n *= len(lst)
    return n


if __name__ == "__main__":
    print(f"{combinations():,} combinations")
    for _ in range(5):
        print("-", make_prompt()[0])
