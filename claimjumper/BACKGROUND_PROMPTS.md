# CLAIMJUMPER — v7 Background Prompts

Firefly prompts for the five wave backgrounds, depicting environmental degradation in the Boise and Salmon River valleys from the arrival of European traders, speculators, miners, and military personnel. Each background renders as both the wave-intro card and the live PLAY scene itself, with the tower and pier composited separately on top — so every prompt keeps human figures out of the scene (that's what causes visual clashes with the separately-rendered player/miner sprites), while industrial structures, camps, and machinery are intentional for the later levels, meant to read as ambient scenery rather than characters. A wide landscape aspect ratio (roughly 8:5) matches how these render in-game.

All five open with the same style anchor, kept word-for-word across the set, so the sequence reads as one consistent world rather than five unrelated images.

## Style anchor (opens every prompt below)

> Retro pixel-art video game background illustration, clean bold linework, cel-shaded blocky coloring, warm saturated hand-painted palette, soft directional ambient light, crisp edges with no anti-aliasing blur, in the style of 16-bit-era adventure game key art. Wide landscape composition of a forested river valley, horizon-line framing, no people, no text, no watermark, no UI elements.

## Level 1 — 15,000 BCE — The Untouched River

> [style anchor] + A pristine glacial river valley at first light, the water so clear the stone riverbed is visible straight through it, and the shallows are almost solid with silver-flanked salmon and trout, fin to fin, more fish than open water. Steep granite walls draped in moss, old-growth conifers crowding right down to the bank, no trail, no clearing, no sign a human hand has ever touched this place. A glacier or lingering snowfield glows on a distant peak, feeding the current with white meltwater. Soft golden dawn light, mist rising off the pools, absolute wilderness silence.

## Level 2 — 1066 A.D. — A Different Bend, Still Whole

> [style anchor] + A different bend of the same forested river valley, still lush and healthy, the water still running clean over stone, salmon still moving through the pools in visible numbers — plainly fewer than an impossibly overstuffed river, but still a river teeming with life. The only trace of people: a simple woven willow fish-weir staked across a side channel, and a dugout canoe pulled up and resting on the bank, its wood worn smooth. No structures, no smoke, no clearing — just the first faint fingerprint of a people who take only what they need. Same warm, unhurried daylight as an older, wilder version of this same place.

## Level 3 — 1804 A.D. — First Scars

> [style anchor] + The same river valley now showing its first wounds: a patch of raw stumps where old growth used to stand, a crude wooden sluice box and rocker cradle staked into the near bank, the water beside it gone cloudy and silt-brown where the current used to run clear. Upriver the forest is still intact, but the near ground is trampled and bare. A canvas tent camp with a plain flag sits at a distance across the water, thin smoke rising from a cookfire. The sky has gone flatter and grayer, the light cooler than before — a valley that has stopped being lived-with and started being surveyed, measured, claimed.

## Level 4 — 1863 A.D. — Gold Camp

> [style anchor] + A gold-rush mining camp overtaking the riverbank: a network of sluice boxes and a raised wooden flume diverting the current, mud-churned water running the color of rust, and a rough shanty skyline crowding the middle distance — canvas tents, plank-board shacks, a two-story false-front building standing in for a saloon, all thrown up crooked and fast. The hillsides above have been stripped and blasted bare in patches, raw dirt and shattered rock where forest canopy used to be, and what timber remains stands as a field of fresh stumps. Harsh, dusty daylight, a haze of woodsmoke and disturbed earth hanging over everything — a valley being worked hard and given nothing back.

## Level 5 — 1927 A.D. — What's Left

> [style anchor] + The same river valley reduced to a wasteland: mile after mile of rounded gray dredge tailings piled in long snaking windrows across what used to be the floodplain, and a massive rust-streaked bucket-line dredge looming in the middle distance, gnawing at the last unworked ground. The river itself is choked to a stagnant, silted trickle threading between the tailing piles, dammed and diverted, utterly empty of fish. The surrounding mountainsides are shorn of forest — crosshatched with logging roads, eroded gullies, and stump fields stretching to the ridgeline, with a concrete dam wall visible far upstream. Flat, bleak overcast light near dusk, a desaturated palette of grays, rust, and mud — the same valley from the very first scene, but with every living thing in it stripped, dammed, or buried.

## Design notes

- **Level 5 deliberately echoes Level 1's composition** (same valley, same implied vantage point) rather than being a totally new scene — that's the payoff: the player should be able to recognize it's the *same place*, just devastated, which lands harder than a generic wasteland would.
- **Level 2's human trace is kept to a fish-weir and a canoe**, not anything European/1066-specific, since 1066 is functioning here as a "long ago, recognizable date" anchor rather than a literal historical claim about this specific river.
- **Level 3 stays light on the disease angle visually** (hard to depict respectfully and unambiguously in a background image) and carries that weight through environmental scarring instead — worth another pass if that history should be represented more directly.

## Open follow-up

Once the actual generated backgrounds are in hand and wired into `claimjumper/assets/`, the in-game wave-intro year labels (currently `1492 A.D.` / `1776 A.D.` / `1863 A.D.` for waves 3-5, set in `claimjumper/index.html`'s `WAVES` array) should be updated to `1804 A.D.` / `1863 A.D.` / `1927 A.D.` to match this timeline — confirmed with the user, not yet done since the code shouldn't drift ahead of the art it's describing.
