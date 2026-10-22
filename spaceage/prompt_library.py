"""Hand-written, detailed image prompts (quality over quantity).

Each entry is a complete art brief: subject, construction details, setting,
light, palette, medium and composition. The poster picks entries at random,
so the owner still does not know which image comes next.
"""

PROMPTS = [
    ("Fortress freighter",
     "A colossal interstellar freighter shaped like a flying fortress, its hull built from thousands of weathered "
     "ivory and sand-colored armor plates, recessed hangar bays, rows of tiny lit portholes, antenna masts and "
     "heat radiators bristling from the upper decks, faded red identification squares painted on the flanks. "
     "Seen from a dramatic low angle so it towers over the viewer. A small black courier ship flies alongside "
     "for scale, leaving a faint vapor trail. Behind it a blazing nebula of saffron, amber and hot magenta with "
     "scattered bright stars. Painted in the style of a 1970s British science fiction paperback cover: "
     "airbrushed acrylic on illustration board, crisp hard-surface edges, soft atmospheric gradients, subtle "
     "paint grain, rich saturated color, museum-quality detail, no text."),
    ("Black hole station",
     "A sprawling deep-space research station assembled from cylindrical pressure tanks, boxy habitat modules, "
     "truss frameworks and radiator fins, painted in oxidized steel blue and rusted copper, with warm lights "
     "glowing in a few windows. The station fills the lower right of a strong diagonal composition. In the "
     "upper sky a black hole bends the light around it, ringed by a thin glowing orange accretion disk, set "
     "in a vast crimson nebula with wisps of scarlet gas. A long chain-like orbital structure crosses the sky "
     "in the far distance. Classic 1980s science fiction book cover painting, meticulous mechanical detail, "
     "dramatic rim lighting, deep reds and cold blues, airbrushed gouache, no text."),
    ("Desert glider",
     "A sleek white atmospheric spacecraft with a wedge-shaped nose, long thin swept-back wings tipped with "
     "violet fins and a bulky engine block underneath, red circular insignia on its tail fin, hovering a few "
     "meters above a cracked red desert plain dotted with dark volcanic rock formations. The sky fades from "
     "deep black with a scatter of stars at the top to burning orange and scarlet at the horizon, with three "
     "moons of different sizes and a giant golden crescent planet rising behind the ship. Hand-painted 1982 "
     "gouache illustration for a science fiction paperback, clean precise rendering of the craft, visible "
     "brush texture in the ground, warm saturated palette, no text."),
    ("Camouflage carrier",
     "A gigantic blocky battle carrier floating in space, its slab-sided hull painted in mint-green and teal "
     "digital camouflage with bold orange racing stripes and large orange numerals, flat landing decks "
     "jutting out like shelves, a rotating radar dish, rows of hangar doors and tiny running lights along "
     "the keel. It drifts through a glowing sky of red, orange and gold nebula clouds sprinkled with soft "
     "white stars, lit warmly from below. Vintage 1970s science fiction paperback cover art, airbrushed "
     "acrylic, crisp geometric shapes, bold graphic color contrast, slightly grainy print texture, no text."),
    ("Hyperspace dive",
     "A dark streamlined warship shaped like a giant submarine with a tall angular bridge tower, swept "
     "stabilizer fins and a large turbine engine at the stern, thin glowing red trim lines tracing its hull "
     "panels. It dives forward out of a luminous turquoise and cobalt hyperspace tunnel streaked with long "
     "white light trails and drifting sparks, seen from a low three-quarter angle so the bow points toward "
     "the viewer. 1980s Japanese space opera anime background painting, hand-painted cel style, deep "
     "blue palette with electric cyan highlights, cinematic depth, no text."),
    ("Generation ship",
     "The curved silver hull of an enormous generation ship fills the lower half of the frame, its surface "
     "flowing with organic sculpted ridges and covered in thousands of tiny warm-lit windows like a city at "
     "night, soft engine glows trailing behind. Ahead lies a deep blue ocean planet with swirling white storm "
     "systems and island chains, a bright white star blazing to the left and a tiny distant companion star. "
     "Rich black space with a faint violet milky way. Elegant digital airbrush illustration in the tradition "
     "of 1990s science fiction book covers, luminous, calm and majestic, cool blue and silver palette, no text."),
    ("Mushroom megastructure",
     "A dark industrial starship built from stacked rectangular hull sections, gantries and landing struts "
     "hovers just above a rocky brown ridge in the foreground. Behind it rises an immense alien megastructure "
     "shaped like a mushroom cloud of smooth stone, its underside dotted with countless faint lights, its "
     "top catching the glow of a hidden sun. Deep teal and midnight blue night sky with a few stars. Painted "
     "in a moody retro science fiction style with flat graphic shapes, muted blue-green palette, gouache "
     "texture, strong silhouettes and a sense of enormous scale, no text."),
    ("Sky sphere city",
     "A giant floating spherical city covered in a fine grid of blue panels, pipes, exhaust stacks and "
     "balconies, a tangle of machinery clinging to one side, hovers above a wide sunny plaza. Colorful "
     "balloons drift around it, a silver airship cruises in the clear blue sky, tiny figures and a red "
     "retro-futuristic truck stand on the plaza, white modernist towers line the horizon. 1980s Japanese "
     "retro-futurist illustration, clean airbrush rendering, bright optimistic daylight, pastel blues with "
     "red and yellow accents, whimsical and highly detailed, no text."),
    ("Pink colossus",
     "A colossal pink and violet architectural arch, part of an unimaginably large structure, towers over a "
     "pale sandy desert. A small dark airship with an orange cabin and spherical gas tanks vents plumes of "
     "white steam as it maneuvers beside a giant circular port in the structure. A crowd of tiny figures "
     "gathers far below for scale. Hazy lavender air, soft diffused light, a pale blue curve of a planet "
     "faintly visible in the sky. Loose painterly gouache concept painting with confident broad strokes, "
     "atmospheric perspective, dreamy pastel palette, no text."),
    ("Broken Dyson sphere",
     "Three enormous curved fragments of a shattered Dyson sphere drift apart in space, their inner surfaces "
     "covered with blue oceans, green continents and swirling white clouds, their outer shells made of black "
     "machinery, thrusters and docking towers. Between them a blazing yellow sun throws out a white corona "
     "and streaks of light across a fiery orange and gold background. Two tiny debris pieces float in the gap "
     "for scale. 1980s science fiction book cover painting, airbrushed acrylic, strong graphic composition, "
     "hot orange against deep blue, meticulous detail, no text."),
    ("Sphere assault",
     "A squadron of flat triangular wedge-shaped starfighters with red panel markings and glowing white "
     "engines attacks a gigantic pale blue spherical battle station covered in an intricate maze of panel "
     "lines, trenches and docking ports. One fighter fires, triggering an explosion that sprays black debris "
     "from the station's surface. A pink and violet nebula and a distant small blue planet fill the "
     "background, scattered with lens-flare stars. Classic late-1970s science fiction illustration, "
     "airbrushed, sharp hard-surface rendering, cool palette with red accents, no text."),
    ("Saucer over the city",
     "A polished silver flying saucer with a domed top and a glowing pink rim hovers high above Earth at "
     "night beside a long black cylindrical rocket whose engine glows soft white. Far below, the lights of a "
     "coastal city spread like golden veins through scattered clouds, and the curved horizon fades into a "
     "purple sky with a single bright star. 1980s airbrushed science fiction painting, smooth reflective "
     "metal rendering, dramatic height and depth, deep blues with warm city lights, no text."),
    ("Golden descent",
     "A gigantic ornate starship of cream-colored metal, with domed observation towers, layered sponsons, "
     "intricate panel engravings and a glowing red sensor eye, descends slowly through a vertical column of "
     "golden light. Below it stretches a dark gothic alien city of needle-thin black spires with tiny lights. "
     "The air is thick with warm orange haze and drifting dust. Epic fantasy-science-fiction book cover "
     "painting in oils, extreme detail, monumental scale, warm amber and ochre palette with deep shadows, "
     "no text."),
    ("Engine cluster",
     "A heavy interstellar ship seen from behind and slightly above, its stern dominated by a cluster of six "
     "hexagonal engine pods blazing with brilliant white light, its hull of dark armored plates with yellow "
     "edge highlights and small sensor masts. Ahead it approaches a long cylindrical space station silhouetted "
     "against a huge fiery red-orange sun with a turbulent surface. Deep blue starfield with faint nebula. "
     "Precise 1990s science fiction book cover painting, airbrushed acrylic, strong backlighting, glowing "
     "engines, no text."),
    ("Mountain launch",
     "A sleek white spaceship with a long needle nose and a cylindrical engine section blasts off diagonally "
     "across the frame on a jet of red and white exhaust, passing a swirling orange gas planet. On the left a "
     "tall slender silver rocket stands on its fins among jagged snow-covered mountain peaks, with dark pine "
     "trees in the foreground and a small blue-green planet in the starry black sky. 1979 science fiction "
     "magazine cover painting, crisp airbrushed acrylic, icy blues against hot orange, no text."),
    ("Moon rocket",
     "A tall retro rocket with three swept fins, a riveted silver hull, round porthole windows and two "
     "brass-gold bands stands on a cratered lunar plain, casting a long shadow. A huge full moon with "
     "detailed maria hangs in a black sky full of golden four-pointed stars. Rendered as a vintage "
     "etching-style illustration in black ink with gold and parchment tones, fine crosshatching, "
     "lithograph texture, elegant and nostalgic, no text."),
    ("Waterfall tower",
     "A retro-futuristic tower station with a weathered copper dome, wraparound observation windows and "
     "smaller bubble pods stands on a single tall pylon at the very edge of a colossal waterfall that pours "
     "into a misty canyon. The cliffs are rust-colored rock with patches of green shrubs, the river above "
     "spreads into a wide shallow delta, and fair-weather clouds drift through a bright blue sky. Highly "
     "detailed 1980s science fiction painting with a pointillist texture, warm copper against cool blue "
     "water, sense of height and spray, no text."),
    ("Forest dome saucer",
     "A large silver flying saucer carrying a transparent glass dome filled with a living pine forest floats "
     "above an alpine lake. A row of warmly lit windows runs around its rim. Behind it rise snow-capped "
     "mountains wrapped in low clouds, and a bright sun flares through the dome. The foreground has pine "
     "trees, red autumn bushes and a calm turquoise lake reflecting the sky. Vintage 1970s science fiction "
     "print with slightly faded colors, scanned paper texture and soft halftone grain, no text."),
    ("Mars megastructure",
     "A towering weathered megastructure of green-painted metal rises from a vast space platform, its facade "
     "carved into deep vertical trenches lit by cold blue interior lights, with tiny walkways, cargo lifts "
     "and maintenance drones. Small shuttles streak past with light trails. Behind it hangs a giant rust-red "
     "planet with detailed craters and canyons, filling half the sky. Dark industrial hull sections frame "
     "the foreground. Cinematic science fiction concept art, photoreal materials, hard rim light, chipped "
     "paint and grime, emerald green against rust orange, no text."),
    ("Floating castle",
     "A floating city of gothic silver spires, stacked towers and buttresses rests on huge bulbous hover pods "
     "with soft glowing undersides, drifting above the curved horizon of a rust-orange desert planet. Pure "
     "black space surrounds it, with a dramatic rim light from an unseen sun picking out every pinnacle. "
     "Dark cinematic science fiction concept art, silver and charcoal with warm orange below, high detail, "
     "majestic and eerie, no text."),
    ("Space armor soldier",
     "A futuristic infantry soldier in a rounded white helmet with orange tinted goggles and a breathing "
     "mask, padded blue-grey armor, a large pauldron with a stenciled red unit number, heavy backpack with "
     "fuel tanks, coiled hoses and a folding shovel, gloves and muddy combat boots, stands in fresh snow. "
     "Painted in confident loose gouache strokes on white paper, unfinished pencil lines at the edges, "
     "military concept illustration style, cool blues with warm tan cloth, no text."),
    ("Classic space scene",
     "A dramatic space scene rich in detail and vibrant color. A large futuristic spacecraft dominates the "
     "foreground, its hull intricately detailed with patterns and structures suggesting advanced technology, "
     "punctuated by red and orange lights. Behind it, outer space swirls with dark blue, black and brown "
     "cosmic dust like a dense nebula. A planet with a bluish-grey surface fills the lower part of the image "
     "for scale and grandeur, and a bright distant star adds stark contrast and depth. Classic science "
     "fiction illustration blending realism and fantasy, painted, highly detailed, no text."),
    ("Asteroid escape",
     "A sleek silver starship with a pointed nose cone, two stabilizer fins and red circular hull markings "
     "bursts out of a tunnel bored into a rugged asteroid, just as two massive titanium blast doors close "
     "behind it, sealing the exit with a glowing orange energy field. The asteroid surface is rough and "
     "cratered with visible striations. The ship's polished hull reflects a vivid purple and pink nebula "
     "scattered with twinkling stars. Tension of escape against a serene cosmos. 1980s science fiction cover "
     "painting, airbrushed, dynamic diagonal, no text."),
    ("Crimson launch",
     "A retro-futuristic cylindrical spaceship with sleek polished metal surfaces blasts off from a desolate "
     "alien desert toward the upper right corner, leaving a trail of orange-yellow flame and billowing smoke. "
     "A huge jagged rock formation of reddish-brown stone dominates the left foreground, smaller rocks are "
     "scattered across the sandy ground, and the vast crimson sky darkens into star-filled black space. "
     "Vintage science fiction illustration from the 1980s with a grainy, well-preserved postcard texture, "
     "deep reds and blacks, no text."),
]
