"""Hand-written image prompts in the spirit of golden-age science fiction.

Four themes, 15 prompts each: the cosmic awe of Arthur C. Clarke, the
Victorian scientific romance of H. G. Wells, the galactic empires and robots
of Isaac Asimov, and the painted covers of German SF pulp magazines of the
1960s-80s. Themes and moods are described in our own words; no protected
names, characters, titles or artist names go into the prompts.
All compositions are vertical (9:16 reels). The poster picks entries at
random, so the owner does not know which image comes next.
"""

CLARKE = "Clarke"
WELLS = "Wells"
ASIMOV = "Asimov"
PULP = "Pulp"

_CLARKE_STYLE = ("Painted in the style of 1970s hard science fiction book cover art, precise and realistic "
                 "space-age engineering, calm majestic mood, sense of cosmic wonder and scale")
_WELLS_STYLE = ("Painted like a Victorian scientific romance illustration from the 1890s to 1900s, oil paint "
                "with fine engraving-like detail, sepia, brass and gaslight tones, dramatic and mysterious")
_ASIMOV_STYLE = ("Painted as a 1950s to 1970s science fiction paperback cover, clean optimistic atomic-age "
                 "futurism, sleek chrome and glowing panels, thoughtful and grand")
_PULP_STYLE = ("Painted as a 1960s to 1980s German science fiction pulp magazine cover, vivid airbrushed "
               "gouache, bold saturated colors, dynamic diagonal composition, adventurous space-opera energy")

_PROMPTS = {
    CLARKE: [
        ("Moon excavation",
         "A perfectly black rectangular monolith, utterly smooth, stands upright in a floodlit excavation pit on the "
         "Moon. Astronauts in white suits stand at its base, tiny against it, one raising a hand toward it. Lunar "
         "night, harsh white floodlights, Earth hanging half-lit in the black sky above the crater rim."),
        ("Inside the cylinder",
         "The interior of a gigantic hollow cylindrical alien vessel, fifty kilometers long: cities and fields "
         "cover the curved inner walls that rise overhead on every side, a band of sea rings the middle, and "
         "long lines of light run along the axis. A tiny human exploration team stands on a stairway in the "
         "foreground, looking up in awe."),
        ("Space elevator dawn",
         "A space elevator ribbon rises from the summit of a sacred mountain on a tropical island, a climber "
         "capsule glinting halfway up as dawn breaks, the tether vanishing into a deep violet sky where an "
         "orbital station catches the first sunlight. Monks and engineers watch from a stone terrace below."),
        ("Wheel station",
         "A great rotating wheel-shaped space station turns slowly above the blue curve of Earth, its spokes and "
         "rim lit by the Sun, a winged shuttle gliding toward the central docking hub with tiny attitude jets "
         "firing. Crisp black space, brilliant sunlight on white panels."),
        ("The overlords arrive",
         "Silent immense silver ships hang motionless above a great city at dusk, one above every capital, "
         "casting long shadows over crowds that stand in the streets looking up. No weapons, no lights, only "
         "an overwhelming calm presence filling the vertical sky."),
        ("Sunjammer race",
         "A racing spacecraft with a single enormous circular solar sail of mirror-thin film, kilometers wide, "
         "glides past the Moon, its rigging lines catching the light, the tiny gondola glowing beneath it. Deep "
         "black space, golden sunlight, other sails like distant silver coins."),
        ("Dust cruiser",
         "A boxy lunar dust-cruiser vehicle skims across a sea of fine grey moondust inside a vast crater, "
         "leaving a faint wake, tourists visible through its large panoramic windows, the crater walls glowing "
         "in low sunlight and Earth rising behind the peaks."),
        ("The stars go out",
         "High in the snowy mountains, monks in red robes and two engineers stand on the terrace of a remote "
         "monastery and look up at a night sky where the stars are silently going out one by one. A large "
         "computer console sits in the open doorway behind them. Quiet, solemn, overwhelming."),
        ("Eternal city",
         "A gleaming eternal city of slender white towers and glass domes rises from an endless desert under a "
         "pale sky, a billion years in the future, no roads leading in or out. A single traveler on a dune looks "
         "toward it. Serene, timeless, crystalline light."),
        ("Ocean ranch",
         "A small yellow submarine glides through the deep blue ocean alongside a herd of great blue whales, "
         "its warden watching through a round viewport, shafts of sunlight falling from the surface far above. "
         "Calm, vast and gentle."),
        ("Jupiter descent",
         "A slender exploration spacecraft with a long boom, round habitat module and dish antenna drifts past "
         "the colossal banded face of Jupiter, the Great Red Spot below, a small icy moon crossing in front. "
         "Precise, luminous, realistic."),
        ("Europa ice",
         "A robotic lander with spindly legs stands on the cracked ice plains of Europa, its lamp shining down "
         "into a fresh fissure where a faint blue glow rises from the hidden ocean below. Jupiter fills the "
         "black sky above, banded and immense."),
        ("Radio telescope signal",
         "A valley of giant radio telescope dishes at night, all turned toward the same point in the starry sky, "
         "a thin band of the Milky Way overhead, scientists gathered at a lit control building in the foreground "
         "staring at a single bright star. Quiet anticipation of first contact."),
        ("Lunar city at earthrise",
         "A city of low domes and gleaming towers built into the rim of a lunar crater, glass walkways linking "
         "them, a passenger spaceliner rising on pale flame from the spaceport, and a blue-white Earth rising "
         "above the grey mountains."),
        ("Ship of the void",
         "A long, needle-like interstellar ship with a giant circular radiation shield at its bow and a cluster "
         "of glowing fusion engines at its stern coasts silently between the stars, a faint pink nebula ahead. "
         "Minimal, lonely, immense."),
    ],
    WELLS: [
        ("Tripods at dusk",
         "Three gigantic Martian fighting machines on tall jointed metal legs stride over a burning Victorian "
         "English village at dusk, their hooded heads glowing, a heat-ray beam slicing across the rooftops. "
         "Terrified villagers in Victorian clothes flee along a country lane in the foreground."),
        ("The cylinder",
         "A huge metal cylinder from Mars lies half-buried in a smoking sandpit on an English common at dawn, "
         "its lid slowly unscrewing, a curious crowd of Victorian onlookers with bowler hats and parasols "
         "gathered around the rim, a policeman holding them back."),
        ("The time machine",
         "A gleaming time machine of polished brass, ivory and quartz rods with a saddle-like seat and spinning "
         "dials stands in a Victorian laboratory lit by gaslamps, a whirl of faint light around it as it begins "
         "to vanish, the inventor in a waistcoat gripping its lever."),
        ("Far future shore",
         "A desolate beach in the unimaginably far future under a huge dim red sun, the sky deep and dark, a "
         "lone brass time machine standing on the shingle, strange giant crab-like creatures crawling on the "
         "rocks, a cold flat sea. Haunting, silent, ancient."),
        ("Ruined palace of the future",
         "A vast crumbling palace of green porcelain and white marble in an overgrown paradise of the far "
         "future, gentle people in pale tunics gathered on its steps among giant flowers, while dark well "
         "shafts lead down into the earth. Golden afternoon light with an undertone of menace."),
        ("Sphere on the Moon",
         "A riveted metal sphere with glass portholes and shutters has landed in a lunar crater at dawn, two "
         "Victorian gentlemen in heavy coats climbing out onto the snow-covered ground, strange plants bursting "
         "from the soil as the sun rises. Wonder and adventure."),
        ("Moon caverns",
         "Vast glowing caverns beneath the Moon's surface, a luminous blue river flowing through a city of "
         "spiral galleries, insect-like moon dwellers working great machines, two Victorian explorers hiding "
         "behind a rock and watching in amazement."),
        ("War in the air",
         "A fleet of giant cigar-shaped airships with gondolas and propellers bombards a city of skyscrapers "
         "from the sky, smoke rising, small biplanes darting between them, searchlights crossing the clouds. "
         "Early twentieth-century illustration feel, sepia and fire."),
        ("White city of tomorrow",
         "A shining white city of the future built into a hillside, terraces, glass lifts and aerial walkways, "
         "men and women in simple flowing clothes, a great gun-like launch tube pointing at the Moon on the "
         "horizon. Visionary 1930s optimism, clean light."),
        ("The sleeper wakes",
         "A colossal future city under a great glass roof, endless tiers of walkways, gigantic wind vanes and "
         "flying machines, crowds of workers in blue, a lone man in old-fashioned clothes standing at a "
         "balcony railing staring down in disbelief."),
        ("Heat-ray on the river",
         "A tall Martian tripod wades through the river beside a Victorian iron bridge, firing its heat-ray at a "
         "small steamship whose cannons blaze back, steam boiling from the water, smoke filling the sky. "
         "Heroic and desperate."),
        ("Giant wasp country",
         "In a quiet English countryside, enormous wasps the size of small aircraft hover above a farmhouse "
         "garden, giant overgrown plants towering over the hedges, a farmer with a shotgun standing his ground. "
         "Strange, playful and unsettling."),
        ("Red weed London",
         "London after the Martian invasion, overgrown by a spreading crimson alien weed creeping over streets "
         "and buildings, an abandoned tripod standing silent beside a church tower, crows circling. Melancholy "
         "red and grey."),
        ("Martian handling machine",
         "Inside a smoking crater, a spider-like Martian handling machine assembles new metal parts with "
         "many glinting arms, green smoke rising, a hidden Victorian narrator peering through a crack in a "
         "ruined wall. Eerie green and copper light."),
        ("Gaslight laboratory",
         "A cluttered Victorian laboratory at night full of brass instruments, glass tubes, globes and star "
         "charts, a telescope pointing through an open dome at a red planet Mars glowing unusually bright. "
         "Warm gaslight, sense of discovery and dread."),
    ],
    ASIMOV: [
        ("City planet",
         "A planet covered entirely by one continuous city, seen from low orbit at night: an endless web of "
         "metal domes, towers and light, no land or sea visible, only a thin glowing atmosphere, and a stream "
         "of starships descending into it. Imperial, vast and humming."),
        ("Galactic library",
         "An immense library at the heart of a galactic empire, endless galleries of glowing data crystals "
         "spiraling upward into darkness, scholars in long robes walking along narrow bridges, a tiny figure "
         "studying a holographic star map at the center."),
        ("Positronic robot at home",
         "A friendly polished metal robot with a softly glowing face plate stands in a sunny 1950s suburban "
         "living room, holding a little girl's hand while she shows it a picture book, a family dog sleeping "
         "nearby. Warm, nostalgic and gentle."),
        ("Steel caves",
         "An enormous enclosed underground city of the future, layer upon layer of walkways, moving sidewalks "
         "and apartment blocks under an artificial sky, millions of people, a detective and a humanlike robot "
         "partner walking side by side through the crowd."),
        ("Edge of the galaxy",
         "A small planet at the very edge of the galaxy, a modest city of scholars on a quiet sea, and above "
         "it the entire spiral galaxy filling the night sky like a vast glowing whirlpool. Hopeful, "
         "contemplative, lonely."),
        ("Imperial fleet",
         "A fleet of sleek silver imperial starships in perfect formation passes over a ringed world, their "
         "hulls engraved with a sunburst emblem, the flagship's long spine glittering with lights. "
         "Atomic-age elegance, grand and orderly."),
        ("Six suns",
         "A world lit by six suns facing its first night in two thousand years: the last sun sets on the "
         "horizon of a dark city while thousands of stars suddenly blaze overhead, people on rooftops staring "
         "up in awe and fear, torches being lit."),
        ("Robots in the vineyard",
         "On a sparsely populated spacer world, sleek humanoid robots tend endless rows of vineyards and "
         "orchards around a lonely glass villa under a gentle sun, a single human figure watching from the "
         "terrace. Perfect, quiet and slightly eerie."),
        ("Ice from the rings",
         "A small ship with a pilot in a spacesuit tows a gigantic glittering chunk of ice from the rings of "
         "Saturn back toward the inner planets, the planet's rings stretching across the black sky. Bold "
         "frontier spirit."),
        ("Robot craftsman",
         "A tall elegant robot carefully carves a wooden sculpture in a sunlit workshop full of finished "
         "furniture and wood shavings, its metal fingers precise and delicate, a curious old man watching "
         "from the doorway. Thoughtful and warm."),
        ("The great computer",
         "A gigantic computer filling a hall the size of a cathedral, endless banks of blinking lights and "
         "tape reels, technicians in white coats dwarfed beside it, one man standing on a gantry to ask it a "
         "question. Retro-future grandeur."),
        ("Time vault",
         "A sealed circular vault on a distant world, rows of empty chairs facing a glass cubicle where a "
         "glowing holographic image of an old man in a wheelchair appears to address the assembled leaders. "
         "Hushed, dramatic, mysterious."),
        ("Robot on Mercury",
         "A bulky robot in heavy armor walks across the blazing sun-baked rocks of Mercury toward a pool of "
         "shimmering liquid metal, the enormous Sun filling half the sky, two astronauts watching tensely "
         "from the shadow of a cliff."),
        ("Spaceport of the empire",
         "A colossal imperial spaceport with landing towers like silver trees, liners of every size arriving "
         "and departing, a sea of travelers on terraces in flowing clothes, a sunset sky streaked with "
         "contrails. Busy, shining and optimistic."),
        ("Mind of the galaxy",
         "A small group of scientists stands in a dark observatory around a floating glowing model of the "
         "galaxy covered in fine mathematical equations, lines of prediction branching across the stars. "
         "Intellectual, quiet and epic."),
    ],
    PULP: [
        ("Sphere over the capital",
         "A colossal spherical starship, kilometers across, with a thick equatorial ring of engines and "
         "hangar bays, rises above the domed capital of a future Earth at dusk, smaller spheres escorting it, "
         "searchlights sweeping the sky."),
        ("Sphere battle",
         "A space battle between gleaming spherical battleships and a swarm of dark alien wedge-shaped ships, "
         "energy beams criss-crossing, shields flaring blue, a burning planet below and explosions blooming "
         "against the stars."),
        ("Jungle landing",
         "A spherical landing ship rests on extended telescopic legs in a steaming alien jungle of giant "
         "red plants, a squad of explorers in silver spacesuits with bubble helmets and raygun rifles "
         "advancing toward strange ancient ruins, two moons in a green sky."),
        ("Transmitter gate",
         "A gigantic arch-shaped matter transmitter crackling with blue energy stands on an alien plain, "
         "explorers in spacesuits stepping out of the shimmering field, strange glowing crystals all around "
         "and a ringed planet overhead."),
        ("Hangar of giants",
         "Inside a vast orbital shipyard hangar, a spherical starship sits in a giant cradle with its "
         "equatorial ring lit, workers and robots on gantries, small shuttles flying in and out through a "
         "huge open gate showing the stars."),
        ("Insect invaders",
         "Huge insect-like alien warriors in chitin armor storm a domed frontier outpost on a rocky desert "
         "world, defenders in spacesuits firing energy weapons from the walls, a spherical ship lifting off "
         "in the background."),
        ("Mutant squad",
         "A small team of space heroes in sleek uniforms stands on a cliff overlooking an alien city at "
         "night, one levitating a boulder with glowing hands, another teleporting in a burst of light, "
         "tense and determined. Adventurous and colorful."),
        ("Tractor beam",
         "A small silver scout ship is caught in the green glowing tractor beam of a gigantic dark alien "
         "mothership, the pilot visible through the cockpit glass, lightning-like energy crackling around "
         "the beam."),
        ("Nova",
         "A star exploding into a brilliant nova, rings of fire racing outward, while a fleet of refugee "
         "starships flees at full thrust toward the viewer, hulls lit red-gold by the blast. Drama and "
         "motion."),
        ("Robot war",
         "Towering combat robots stride through the smoking ruins of a frontier colony, red eyes glowing, "
         "while a lone astronaut hero with a raygun crouches behind a wrecked hover vehicle. Thrilling and "
         "dangerous."),
        ("Ice planet base",
         "A domed research base on a frozen blue ice planet under a pale double sun, a spherical starship "
         "landing on blazing thrusters that kick up clouds of snow, explorers in orange suits waving "
         "beside snow crawlers."),
        ("Crater city",
         "A futuristic city under a giant transparent dome inside a vast crater on a barren red world, "
         "monorails, towers and gardens glowing inside, a stormy dust sky outside and a spaceship "
         "approaching the dome gate."),
        ("Ancient alien arcology",
         "Explorers in spacesuits with lamps enter an ancient alien megastructure half buried in desert "
         "sand, colossal carved gateways and glowing machines still running after millions of years, "
         "their spherical ship tiny on the horizon."),
        ("Space pirates",
         "Sleek black space pirate ships with red markings attack a heavy freighter near an asteroid belt, "
         "boarding tubes extending, laser fire everywhere, a heroic patrol ship racing in from the "
         "foreground."),
        ("Alien princess world",
         "A fantastic alien palace of crystal spires on a floating island above a sea of clouds, a "
         "spherical starship docked at its landing tower, two moons rising, exotic flying creatures circling. "
         "Romantic, colorful space opera."),
    ],
}

_STYLES = {CLARKE: _CLARKE_STYLE, WELLS: _WELLS_STYLE, ASIMOV: _ASIMOV_STYLE, PULP: _PULP_STYLE}
_ENDING = "Tall vertical composition, no text, no lettering."

# (title, full prompt) pairs with each theme's own cover style; used by the
# FLUX test workflow and as one of the looks in STYLES below.
PROMPTS = [
    (f"{theme}: {title}", f"{text} {_STYLES[theme]}. {_ENDING}")
    for theme, entries in _PROMPTS.items()
    for title, text in entries
]

# Scenes without a style, so autogen.py can combine any scene with any look.
SCENES = [(f"{theme}: {title}", text) for theme, entries in _PROMPTS.items() for title, text in entries]

# Very different visual styles, described in our own words (no artist names).
STYLES = [
    ("painted cover", _CLARKE_STYLE),
    ("victorian romance", _WELLS_STYLE),
    ("atomic age paperback", _ASIMOV_STYLE),
    ("german pulp", _PULP_STYLE),
    ("photoreal film still", "Photorealistic cinematic film still shot on 65mm IMAX, anamorphic lens flares, "
     "volumetric light, shallow depth of field, rich film grain, epic blockbuster lighting"),
    ("kodachrome", "Authentic 1960s Kodachrome slide photograph, warm saturated colors, slight vignette, "
     "dust and scratches, as if taken by an astronaut with a medium format camera"),
    ("soviet poster", "Soviet space-race propaganda poster, bold flat shapes, red, cream and black, "
     "heroic upward perspective, screen-printed texture, constructivist geometry"),
    ("ukiyo-e", "Japanese ukiyo-e woodblock print, flat areas of indigo, vermilion and ochre, "
     "elegant outlines, stylized waves and clouds, visible washi paper grain"),
    ("anime cel", "1980s hand-painted anime cel, crisp ink lines, airbrushed backgrounds, "
     "dramatic speed lines and lens flares, nostalgic VHS color"),
    ("ligne claire", "Franco-Belgian ligne claire comic panel, clean uniform ink outlines, flat bright colors, "
     "meticulous detailed backgrounds, sunny adventure mood"),
    ("art deco poster", "Art deco travel poster, streamlined geometric forms, gold, teal and black, "
     "elegant gradients, luxurious 1930s glamour"),
    ("blueprint", "Technical blueprint drawing, white precise lines on deep blue paper, cutaway views, "
     "measurement annotations as abstract marks, engineering elegance"),
    ("watercolor", "Loose expressive watercolor painting, soft bleeding washes, white paper showing through, "
     "delicate granulation, dreamy atmosphere"),
    ("linocut", "Bold black-and-white linocut print with one accent color, carved gouge marks, "
     "strong contrast, handmade printmaking texture"),
    ("airbrush on board", "Hand airbrushed illustration on illustration board from the early 1980s, soft overspray, masking-film edges, tiny paint specks, slightly faded colors"),
    ("cyberpunk night", "Rain-soaked cyberpunk night photography, neon signs reflected in puddles, "
     "haze and steam, teal and orange color grade, gritty and dense"),
    ("matte painting", "Classic hand-painted matte painting for a 1970s epic film, monumental scale, "
     "painterly glass-shot look, subtle atmospheric perspective"),
    ("risograph", "Risograph print in three spot colors (fluorescent pink, blue and yellow), slight misregistration, "
     "grainy halftone texture, indie zine look"),
    ("stained glass", "Gothic stained glass window, thick lead lines, glowing jewel-colored glass, "
     "light streaming through, cathedral grandeur"),
    ("oil impasto", "Thick expressive oil impasto painting, heavy palette-knife strokes, vibrant broken color, "
     "visible canvas texture, emotional and bold"),
    ("charcoal", "Dramatic charcoal and graphite drawing on toned paper, smudged shadows, white chalk highlights, "
     "raw sketchbook energy"),
    ("claymation", "Handmade claymation diorama, plasticine figures with fingerprints, miniature practical sets, "
     "warm studio lighting, stop-motion charm"),
    ("tilt-shift", "Tilt-shift miniature photograph, selective focus making everything look like a tiny model, "
     "bright toy-like colors, overhead angle"),
    ("infrared", "Surreal infrared photograph, pink and white foliage, deep dark skies, otherworldly glow, "
     "fine-art photography print"),
    ("double exposure", "Artistic double exposure photograph blending the scene with a vast starfield and nebula, "
     "moody monochrome with one color accent"),
    ("bauhaus", "Bauhaus-inspired geometric composition, circles, triangles and bars in primary colors, "
     "minimal and rhythmic, modernist print"),
    ("mosaic", "Ancient Byzantine mosaic of small glass and gold tesserae, shimmering gold background, "
     "stylized figures, timeless sacred feel"),
    ("polaroid", "Faded instant Polaroid photo, washed-out colors, soft focus, light leaks, "
     "white frame edges cropped out, nostalgic snapshot"),
    ("dieselpunk", "Dieselpunk lithograph, heavy riveted machinery, smoke and soot, muted olive and rust palette, "
     "1940s industrial poster style"),
    ("gouache", "Opaque gouache painting on cold-press illustration board, flat matte color areas, visible brush marks and uneven edges, a few pencil construction lines showing through"),
    ("pen and ink", "Pen and ink drawing with dense cross-hatching and stippling on bristol board, "
     "slightly wobbly hand-drawn lines, occasional ink blots, white-out corrections"),
    ("etching", "Intaglio etching printed from a copper plate, fine engraved lines, plate tone and "
     "plate mark, warm black ink on heavy rag paper"),
    ("colored pencil", "Colored pencil drawing on toned paper, layered strokes with visible direction, "
     "paper grain showing through, smudges near the edges"),
    ("ink wash", "Traditional East Asian ink wash painting, flowing brush strokes, misty empty space, "
     "subtle grey tones with a single red seal-like accent shape"),
    ("screen print", "Hand-pulled screen print in four flat inks on cream paper, slight misregistration, ink build-up at the edges, uneven ink coverage"),
]
# Appended to every generated prompt: push away from the glossy, too-perfect
# digital look towards real materials and the small flaws of handmade work.
STYLE_ENDING = ("Made with real physical materials and techniques, with the natural imperfections of handmade "
                "work: uneven strokes, texture of paper, canvas or film grain, slight asymmetry, natural light, "
                "restrained believable colors. Not a digital render, no CGI gloss, no plastic surfaces, "
                "no over-sharpened details. " + _ENDING)
