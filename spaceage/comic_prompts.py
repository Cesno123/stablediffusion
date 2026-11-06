"""Comic-style image prompts for FLUX (run.py --flux N --set comic).

Three looks, all science fiction, no protected characters (only the style):
  fifties  1950s sci-fi comic: halftone dots, heavy inks, faded print (1-16)
  dark90s  1990s dark comic cover: capes, chains, dense inking, rim light (17-28)
  noir     gothic noir comic: rain, deep blacks, gargoyles, one red accent (29-40)
"""

COMIC = [
    ("fifties-01", 'A chrome rocket ship with red fins blasting off from a crowded launch pad, spectators in hats shielding their eyes, a ringed planet huge in the sky, 1950s science fiction comic book cover, bold ink outlines, Ben-Day halftone dots, flat vintage print colors, slightly misregistered printing, aged paper texture'),
    ("fifties-02", 'Two astronauts in bubble helmets discovering a giant glowing crystal city inside an asteroid cave, one pointing in amazement, 1950s pulp comic panel, heavy black inks, halftone shading, yellow and teal palette, worn newsprint texture'),
    ("fifties-03", 'A giant tentacled alien rising from a methane sea toward a tiny silver rocket, panicked crew at the portholes, 1950s horror science fiction comic cover, dramatic diagonal composition, thick inks, halftone dots, faded red and green print'),
    ("fifties-04", 'A woman in a red flight suit at the controls of a spaceship while a swarm of flying saucers attacks outside the window, 1950s sci-fi comic panel, expressive inked faces, Ben-Day dots, vintage four-color printing'),
    ("fifties-05", 'A robot with a glass dome head carrying a fainted scientist through a burning laboratory, sparks and smoke, 1950s science fiction comic cover, bold lines, halftone shading, aged pulp paper, dramatic red and black'),
    ("fifties-06", 'Explorers in space suits crossing a rope bridge over a glowing lava canyon on an alien moon, a giant planet rising, 1950s adventure comic panel, heavy ink hatching, halftone dots, orange and blue vintage print'),
    ("fifties-07", 'A huge flying saucer hovering over a small American town at night, beams lighting up the main street, people running from a diner, 1950s invasion comic cover, thick inks, halftone, faded yellow and blue'),
    ("fifties-08", 'Inside a rocket cockpit: a pilot pulling a lever as a meteor storm flashes past, radar screen glowing, 1950s sci-fi comic panel, speed lines, bold inks, Ben-Day dots, misregistered color print'),
    ("fifties-09", 'A team of astronauts planting a flag on a strange purple moon while giant creatures watch from the ridge, 1950s pulp comic cover, dramatic low angle, inked shadows, halftone texture, vintage colors'),
    ("fifties-10", 'An underwater city under a glass dome, a submarine-rocket docking, divers with harpoons and sea monsters outside, 1950s science fiction comic panel, bold outlines, halftone, teal and coral palette, aged print'),
    ("fifties-11", 'A giant robot towering over a city skyline, soldiers with ray guns firing from rooftops, 1950s atomic age comic cover, heavy black inks, Ben-Day dots, red yellow and blue vintage print, newsprint grain'),
    ("fifties-12", 'A mad scientist in a goggles mask activating a towering tesla machine in a cave laboratory, glowing tubes and arcs, 1950s sci-fi comic panel, crosshatched shadows, halftone dots, green and yellow print'),
    ("fifties-13", 'A space station shaped like a wheel under attack by alien fighters, laser beams crisscrossing, astronauts floating in panic, 1950s comic book cover, dynamic composition, bold inks, halftone shading, faded print'),
    ("fifties-14", 'Two pilots peering through a cracked canopy at a colossal derelict alien ship drifting in a nebula, 1950s sci-fi comic panel, shocked expressions, heavy inks, Ben-Day dots, dark blue and orange'),
    ("fifties-15", 'A jungle planet with giant mushrooms, a crashed rocket half buried, survivors with ray guns facing a dinosaur-like creature, 1950s pulp comic cover, bold lines, halftone, saturated vintage greens'),
    ("fifties-16", "A rocket racing toward a red dwarf sun, the pilot's face lit red through the window, 1950s science fiction comic splash panel, dramatic close-up, heavy ink shadows, halftone dots, worn paper texture"),
    ("dark90s-17", 'A towering armored space knight with a tattered cape whipping in solar wind, standing on the wreck of a starship, glowing green eyes, chains floating around him, 1990s dark comic book cover art, hyper-detailed inking, extreme shadows, dramatic low angle, gritty texture'),
    ("dark90s-18", 'A demonic biomechanical bounty hunter crouching on a neon-lit space station antenna, giant cape spreading like wings, sparks raining down, 1990s gritty comic cover, heavy black ink, intricate line detail, green and red glow'),
    ("dark90s-19", 'A lone hooded figure walking through a graveyard of crashed spaceships under a blood-red moon, cape trailing, crows on wreckage, 1990s dark comic cover, chaotic detailed linework, deep blacks, red rim light'),
    ("dark90s-20", 'A massive alien warlord on a throne of skulls and machinery inside a dark flagship, chains hanging from the ceiling, 1990s dark comic cover, hyper-detailed inks, dramatic perspective, sickly green light, gritty print texture'),
    ("dark90s-21", 'A cyborg anti-hero bursting through a burning hatch of a space freighter, guns blazing, cape and chains swirling, 1990s action comic cover, extreme foreshortening, heavy inks, motion lines, orange fire against black'),
    ("dark90s-22", 'A dark figure with glowing eyes perched on a gargoyle-shaped satellite above Earth, cape spread across the stars, 1990s gritty comic cover, intricate cross-hatching, cosmic background, cold blue and green'),
    ("dark90s-23", 'A horde of skeletal space marines climbing out of a crashed dropship in fog, one giant leader in front with a cape of chains, 1990s dark comic cover, dense detailed inking, smoke and embers, muted palette with toxic green'),
    ("dark90s-24", 'A hunter in spiked armor confronting a huge tentacled cosmic horror in a derelict cathedral ship, 1990s dark comic splash page, wild flowing lines, deep shadows, sickly purple and green light'),
    ("dark90s-25", 'Close-up of a scarred masked face lit by a burning planet below, cape edges like flames, chains around the neck, 1990s gritty comic cover, extreme detail in the inks, red and black'),
    ("dark90s-26", 'A dark rider on a hover bike tearing through a ruined megacity under alien warships, cape streaming, debris flying, 1990s action comic cover, dynamic diagonal, heavy inks, smoke and neon green'),
    ("dark90s-27", 'A figure in a living symbiotic armor suit floating in zero gravity inside a shattered space station, tendrils reaching out, 1990s dark comic cover art, intricate organic line work, deep black, cold rim light'),
    ("dark90s-28", 'Two dark anti-heroes back to back surrounded by alien creatures on a burning moon base, capes and chains flying, 1990s comic cover, chaotic energy, heavy shadows, orange explosions against black sky'),
    ("noir-29", 'A caped silhouette standing on a gothic spire of a futuristic city in pouring rain, spaceships with searchlights passing below, noir comic book art, stark black and white with a single red accent, heavy brush inks, dramatic vertical composition'),
    ("noir-30", 'A detective in a long coat and fedora walking through a rain-soaked space colony alley, neon signs reflected in puddles, a giant moon above, gothic noir comic panel, deep blacks, minimal blue and red, brush inking'),
    ("noir-31", 'Stone gargoyles on a cathedral-like space station watching a fleet arrive through storm clouds, gothic noir comic cover, high contrast, heavy black shadows, lightning, muted grey with red sky'),
    ("noir-32", 'A dark vigilante gliding with a wide cape between towering gothic skyscrapers on another planet, two moons behind, noir comic splash page, silhouette against the moons, black and deep blue, rain streaks'),
    ("noir-33", 'An interrogation on top of a crashed starship in the rain, a cloaked hero holding a smuggler over the edge of a canyon city, gothic noir comic panel, extreme shadows, harsh lighting, black white and red'),
    ("noir-34", 'A gothic mansion on an asteroid with a huge signal beam projecting a strange symbol into the storm clouds, noir comic cover, rain, lightning, black and slate grey with a yellow beam'),
    ("noir-35", 'A villain in a cracked porcelain mask standing in a flooded subway of a space city, flickering lights, gothic noir comic panel, heavy ink, sickly green accent on black'),
    ("noir-36", 'A caped hero crouching on a ledge watching a monorail cross a bridge above a foggy gothic future city, noir comic art, rain, high contrast, dark blue with red tail lights'),
    ("noir-37", 'A clock tower base on a frozen moon, its giant clock face glowing, a lone figure silhouetted in front, snow and ravens, gothic noir comic cover, black and icy blue, brush inks'),
    ("noir-38", 'A dark hero fighting robots in a burning gothic cathedral turned into a spaceport, stained glass shattering, noir comic splash panel, flames and shadows, black orange and red'),
    ("noir-39", 'A rain-soaked rooftop with a cloaked figure and a giant satellite dish behind, lightning illuminating a mothership in the clouds, gothic noir comic cover, stark silhouette, black and violet'),
    ("noir-40", 'A lone cloaked figure standing over a defeated alien army in a dark ruined city, smoke rising, a single red moon, gothic noir comic splash page, minimal palette, heavy ink and brush texture'),
]
