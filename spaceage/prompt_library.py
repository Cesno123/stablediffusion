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

PROMPTS += [
    ("Ice moon harbour",
     "A deep-space supply ship with a stubby insulated hull, frosted cargo pods and amber floodlights settles onto "
     "a landing ring carved into the ice cliffs of a frozen moon. Plumes of vapor curl from its thrusters, tiny "
     "workers in orange suits wait on a gantry, and the banded gas giant the moon orbits fills half of the "
     "violet sky. Cinematic science fiction concept painting, cold cyan and steel tones with warm amber "
     "accents, crisp mechanical detail, sense of bitter cold and quiet routine, no text."),
    ("Canyon city",
     "A vertical city built into both walls of a red sandstone canyon on an alien world, terraces, hanging "
     "gardens, cable cars and slender bridges strung between the cliffs, tiny hover skiffs gliding below and a "
     "winding turquoise river at the bottom. Two pale moons hang in a dusty apricot sky. Detailed 1970s "
     "science fiction book illustration, warm terracotta and turquoise palette, airbrushed acrylic, deep "
     "perspective looking down the canyon, no text."),
    ("Derelict giant",
     "The broken hull of a colossal ancient warship drifts through a dim asteroid field, its armor plates peeled "
     "back to reveal skeletal ribs and dark corridors, with frozen debris and a cloud of glittering ice "
     "crystals around the breach. A small salvage tug with a single bright searchlight probes the wreck. "
     "Moody cinematic science fiction painting, desaturated greys and rust with one cold white light beam, "
     "eerie silence, rich texture, no text."),
    ("Solar sail regatta",
     "A fleet of slender spacecraft with enormous golden solar sails, thin as foil and shimmering with rainbow "
     "interference, races past a blazing white sun, their sails catching the light like the wings of insects. "
     "The closest ship shows fine rigging lines and a small glowing cabin. Elegant retro-futurist "
     "illustration in the tradition of 1960s space-age art, gold, white and deep navy, luminous and serene, "
     "no text."),
    ("Mech in the rain",
     "A battered bipedal walker mech, twice the height of a house, stands motionless in a flooded city street "
     "at night, rain streaming off its olive-drab armor, a cracked cockpit window glowing faint green, cables "
     "hanging from its shoulder joint. Neon shop signs without readable letters reflect in the puddles, and a "
     "lone figure with an umbrella looks up at it. Cinematic film still, moody teal and magenta lighting, "
     "photoreal wet materials, shallow depth of field, no text."),
    ("Lighthouse station",
     "A tall lighthouse-like beacon station stands alone on a small rocky planetoid at the edge of a spiral "
     "galaxy, its rotating lamp throwing a long beam across space, a tiny cottage-like habitat at its base with "
     "warm windows and a little shuttle parked beside it. The galaxy swirls in rich purples and blues behind. "
     "Storybook science fiction painting, gouache, gentle and lonely mood, warm light against a cool cosmos, "
     "no text."),
    ("Rover at dawn",
     "A six-wheeled exploration rover with a pressurized cabin, solar panels and a mast of antennas crests a "
     "dune on a rust-colored planet at sunrise, its headlights still on, long shadows stretching across rippled "
     "sand. Two astronauts walk ahead with lamps, and a thin blue dawn glows over distant mesas. Vintage NASA "
     "concept art from the 1970s, painterly realism, warm ochre and cool blue, quiet sense of exploration, "
     "no text."),
    ("Orbital shipyard",
     "A massive starship under construction inside an orbital shipyard, its half-finished hull surrounded by "
     "scaffolding frames, robotic welding arms throwing bright sparks, cargo drones carrying hull plates, and "
     "a curved Earth-like planet glowing below with city lights on the night side. Hard-edged science fiction "
     "illustration from a 1980s technical art book, airbrushed, cool silver and blue with orange sparks, "
     "intricate detail, no text."),
    ("Jungle temple ship",
     "An ancient alien starship overgrown with vines and moss rests half sunk in a misty jungle, its curved hull "
     "patterned like a carved temple, giant ferns and glowing blue flowers around it. A small expedition team "
     "with lanterns approaches through the fog, light rays falling through the canopy. Atmospheric science "
     "fiction adventure painting, lush greens with turquoise glow, oil painting texture, sense of discovery, "
     "no text."),
    ("Twin-sun duel",
     "Two sleek starfighters, one white with blue stripes, one black with red, chase each other low over an "
     "endless salt flat under two setting suns, their engine trails glowing, their shadows racing across the "
     "cracked white ground. Dynamic 1980s science fiction cover painting, strong diagonal motion, warm "
     "sunset gradient sky, crisp airbrushed metal, no text."),
    ("Glass dome garden",
     "Inside a vast glass-domed garden on the Moon, terraced fields, fruit trees and a small lake glow under "
     "warm grow lights, while beyond the dome the grey cratered surface and a blue Earth hang in a black sky. "
     "Families stroll along curved paths and a monorail glides overhead. Optimistic retro-futurist "
     "illustration in the style of 1970s space colony art, soft greens and golds against black, highly "
     "detailed, no text."),
    ("Storm planet dive",
     "A heavy armored lander plunges through the churning cloud bands of a giant storm planet, lightning "
     "forking around it, its heat shield glowing orange-white, stabilizer fins extended. Far below, a red "
     "vortex the size of a continent spins. Dramatic science fiction painting, swirling ochre and deep "
     "brown clouds with electric blue lightning, intense motion, airbrushed realism, no text."),
    ("Ringed world sunrise",
     "Sunrise seen from the surface of a moon: the edge of a giant ringed planet rises over a jagged horizon of "
     "dark basalt peaks, its rings a sharp bright line across the sky, a small domed outpost with a glowing "
     "window in the foreground and a lone astronaut planting a beacon. Classic 1950s and 1960s space art, "
     "precise astronomical realism, deep blacks with luminous gold and cream, no text."),
    ("Cargo convoy",
     "A convoy of long boxy cargo haulers linked like a space train moves through an asteroid belt, escorted by "
     "two small arrowhead fighters, navigation beacons blinking along their hulls, one hauler painted in faded "
     "yellow and black hazard stripes. A distant orange star lights the scene from the side. Industrial "
     "science fiction illustration, gritty weathered metal, warm side light and deep shadow, 1980s paperback "
     "cover style, no text."),
    ("Sky whales",
     "Enormous graceful space creatures shaped like whales, their translucent bodies glowing with soft "
     "bioluminescent patterns, glide past a small research ship near a pastel nebula. Tiny drones follow "
     "them taking measurements. Dreamlike science fiction painting, iridescent blues, pinks and pearl white, "
     "soft airbrush gradients, peaceful and awe-inspiring, no text."),
    ("Neon spaceport",
     "A crowded spaceport at night on a rain-soaked megacity rooftop, a scuffed freighter with glowing engines "
     "lifting off between towering skyscrapers, holographic signs made of abstract symbols, steam vents, "
     "pilots and dock workers silhouetted against the light. Cyberpunk science fiction concept art, magenta "
     "and cyan neon, wet reflective surfaces, cinematic depth, no text."),
    ("Monolith plain",
     "A towering black monolith of perfect smoothness stands in the middle of a vast salt plain under a pale "
     "green sky, a ring of small explorers and their parked hover vehicle dwarfed beside it, long shadows "
     "pointing toward the viewer. A faint ring of light hovers above the monolith. Minimal surreal science "
     "fiction painting, restrained palette of black, bone white and sage green, strong geometry, no text."),
    ("Mars greenhouse",
     "A cozy greenhouse habitat on Mars at dusk, rows of tomatoes and herbs under violet grow lights, a robot "
     "gardener with soft rounded shapes watering plants, and through the curved window a dusty red landscape "
     "with a blue Martian sunset. Warm detailed science fiction illustration, inviting interior light, "
     "contrast between green life and red desert, painterly, no text."),
    ("Battle above the moon",
     "Two great fleets clash above a grey cratered moon, capital ships firing streams of glowing tracer fire, "
     "explosions blooming silently, fighters weaving between them, debris spinning in the foreground. The "
     "bright blue limb of a planet curves across the top of the frame. Epic space opera painting, 1980s book "
     "cover style, airbrushed, high contrast oranges and blues, dense detail, no text."),
    ("Underwater base",
     "A research base of linked glowing domes anchored to the sea floor beneath the ice of a frozen moon, a "
     "small submarine with headlights approaching, strange luminous jellyfish-like creatures drifting nearby, "
     "and faint light filtering down through cracks in the ice ceiling far above. Atmospheric science fiction "
     "concept painting, deep teal and black with warm interior lights, sense of mystery, no text."),
    ("Retro rocket parade",
     "Three gleaming retro rockets with tail fins and chrome bands stand ready on launch towers at a coastal "
     "spaceport at dawn, crowds of tiny spectators behind fences, searchlights fading as the sun rises over the "
     "ocean, a flock of seabirds crossing the sky. 1950s pulp science fiction magazine illustration, bold "
     "optimistic colors, peach and turquoise sky, painted gouache, no text."),
    ("Cathedral ship",
     "A vast gothic battleship shaped like a flying cathedral, with spires, flying buttresses, stained glass "
     "windows glowing red and gold, and banks of engines along its keel, drifts slowly through a dark violet "
     "nebula. Small escort ships trail behind it like moths. Dark baroque science fiction oil painting, "
     "dramatic chiaroscuro, deep purples, black and gold, monumental scale, no text."),
    ("Wandering planet",
     "A rogue planet with a thin glowing atmosphere drifts through interstellar darkness, its night side "
     "covered with the lights of scattered cities, while a lone small starship approaches with its landing "
     "lights on. A faint band of the galaxy arcs behind. Quiet contemplative space art, minimal composition, "
     "deep navy and black with warm golden city lights, airbrushed realism, no text."),
    ("Skyhook elevator",
     "A space elevator rises from a green tropical island into the sky, its tether a thin silver line "
     "vanishing into the clouds, a climber pod halfway up catching the sunlight, a station ring visible in "
     "orbit far above. Turquoise sea, white beaches and boats in the foreground. Bright optimistic "
     "retro-futurist poster painting, clean shapes, turquoise, white and sunny yellow, no text."),
    ("Desert caravan",
     "A caravan of tall walking machines with rounded cargo cabins on spindly legs crosses a vast orange desert "
     "at sunset, cloth banners fluttering, robed travelers riding on their decks, a ringed planet low on the "
     "horizon. Long shadows stretch across the dunes. Science fiction adventure painting in the spirit of "
     "European comic albums of the 1970s, clean lines, warm flat colors, wide panoramic view, no text."),
    ("Pilot portrait",
     "Portrait of a weathered starship pilot in a worn flight jacket with mission patches without letters, a "
     "scratched helmet under her arm, standing in a dim hangar, a large fighter's nose cone behind her lit by "
     "warm work lights. Her expression is calm and tired. Cinematic science fiction character painting, "
     "realistic oil technique, warm amber and cool shadow, shallow depth, no text."),
    ("Comet miners",
     "Miners in bulky suits anchor drilling rigs on the surface of a comet, jets of glittering gas and dust "
     "erupting around them, their tethered ship hovering above with floodlights, and the long glowing tail of "
     "the comet stretching across a field of stars. Detailed 1980s science fiction illustration, icy whites "
     "and blues with sodium orange lights, airbrushed, sense of danger, no text."),
    ("Ancient gate",
     "A gigantic ring-shaped alien gate made of dark stone and metal floats in space near a red dwarf star, its "
     "inner edge rippling with a shimmering field of light, a small scout ship approaching cautiously. Strange "
     "carved symbols cover the ring, worn and cracked. Mysterious science fiction painting, deep red and black "
     "with an electric blue glow, airbrushed, epic scale, no text."),
    ("Floating market",
     "A busy floating market in the clouds of a gas giant, airships and small hover barges tied to a central "
     "platform hung with lanterns and colorful awnings, traders exchanging crates, cloud layers glowing peach "
     "and lavender at sunset. Whimsical detailed science fiction illustration, warm festive colors, "
     "painterly, lively atmosphere, no text."),
    ("Last launch",
     "The last rocket leaving a dying, overgrown city at night, its exhaust lighting up abandoned towers covered "
     "in vines, a small crowd watching from a rooftop, fireflies and stars above. Emotional cinematic science "
     "fiction painting, deep greens and blacks with a brilliant white-orange exhaust plume, hopeful and "
     "melancholic, no text."),
    ("Asteroid hermit",
     "A tiny hand-built home on a small asteroid: a patched-together cabin with a round door, a satellite dish, "
     "a vegetable patch under a glass cover and a little shuttle parked beside it, a cat sitting in the window. "
     "The whole asteroid floats against a colorful nebula. Cozy storybook science fiction illustration, "
     "gouache, warm and charming, soft pastel space colors, no text."),
    ("Titan lake",
     "A small exploration boat with a bright orange hull floats on a methane lake on Titan, thick golden haze "
     "overhead, the faint shadow of Saturn visible through the clouds, rounded hills of ice along the shore. "
     "A crew member stands at the bow with a sampling pole. Realistic space art, muted gold, umber and slate, "
     "soft diffused light, quiet and alien, no text."),
    ("Crystal flagship",
     "A colossal wedge-shaped flagship made of white crystal and silver metal emerges from a burst of white "
     "light, its edges glowing, smaller ships scattering from its path, a blue nebula rippling around it like "
     "water. Majestic science fiction concept art, cool white, silver and cobalt, high contrast, cinematic "
     "lens flare, no text."),
    ("Robot repair",
     "Inside a cramped workshop aboard a freighter, an old maintenance robot with chipped yellow paint repairs "
     "a small drone at a workbench, tools hanging on the wall, a round porthole showing stars and a passing "
     "planet. Warm cozy science fiction interior, detailed clutter, tungsten light, painterly illustration "
     "with a nostalgic 1980s feel, no text."),
    ("Crystal canyon",
     "A lone astronaut walks through a canyon of giant translucent crystals that glow from within in pink, "
     "violet and teal, light refracting into rainbows on the ground, a small lander waiting in the distance. "
     "Fantasy science fiction painting, luminous colors, detailed crystal facets, wonder and solitude, "
     "no text."),
    ("Polar launch base",
     "A launch base at the polar circle at night, a slim white rocket on the pad lit by floodlights, aurora "
     "curtains of green and violet rippling across the sky, snow drifting across the concrete and a row of "
     "small red lights along the tower. Cinematic realistic painting, cold blues with vivid aurora colors, "
     "crisp detail, quiet anticipation, no text."),
]
