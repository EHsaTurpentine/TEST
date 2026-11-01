# CLAIMJUMPER — Background Prompts, Flux.1-dev Revision

Nov 1, 2026. Second pass at the five wave backgrounds, rewritten for
Forge running **flux1-dev-fp8** rather than Adobe Firefly, aimed
squarely at the "sloppy and jagged" quality complaint on the first set.
`BACKGROUND_PROMPTS.md` stays as-is — this is a separate revision, not
an edit to it, since that file is the record of what actually shipped
in the current live backgrounds.

## Why Flux changes the prompt shape (not just the words)

Firefly and Flux.1-dev are both capable of reading a natural-language
paragraph instead of a comma-tag list — that part of the old prompts
carries over close to verbatim. What's actually different:

- **Negative prompts barely do anything on flux-dev.** It uses distilled
  guidance, not the classifier-free guidance that makes a classic SD
  negative prompt work. Don't lean on one to fix jaggedness or unwanted
  content — say what you *do* want in the positive prompt instead (see
  "crisp, not jagged" language built into every prompt below).
- **Step count and sampler matter more here than prompt wording for the
  specific "jagged" complaint.** A low step count is the single most
  common cause of visible aliasing/noise/messy edges on Flux — see
  "Generation settings" below before concluding a bad result is a prompt
  problem.
- **Resolution**: Flux-dev was trained on a fixed set of aspect-ratio
  buckets, and none of them is exactly `LW:LH`'s 1.667. Generate at the
  closest native bucket and crop afterward — exactly the same move
  that already worked integrating the Firefly set (those came in at
  1.286 and got cropped up to 1.667; this time the source is wider than
  the target, so the crop trims the sides instead of the top).

## Generation settings (starting point, adjust by eye)

| Setting | Value | Why |
| --- | --- | --- |
| Resolution | **1344x768** (1.75 aspect) | Closest Flux-dev native bucket to 400:240's 1.667; crop ~5% off left+right after, not top/bottom |
| Steps | **28-32** | Flux-dev needs more than SD's old ~20-step habits to resolve fine detail cleanly; this is the first knob to raise if output looks soft or aliased |
| Sampler | **Euler** (or your Forge default for Flux) | The standard, well-tested choice for flux-dev; no strong reason to deviate for this use case |
| Distilled CFG Scale | **~3.5** | Flux-dev's own guidance knob (not classic CFG). Too high tends to oversaturate/crunch edges — exactly the kind of artifact that could read as "jagged"; if a result looks harsh, try lowering before reworking the prompt |
| Negative prompt | Leave blank or minimal | See above — don't expect it to do real work on dev |

If you've got a pixel-art, illustration, or game-background LoRA loaded
alongside the checkpoint, say so and I'll fold its trigger word/weight
into these — I wrote the prompts below assuming base flux1-dev-fp8 with
no LoRA.

## Style anchor (opens every prompt below)

> Painterly video game background illustration, clean crisp linework, cel-shaded blocky coloring with soft directional ambient light, properly rendered sharp edges with no jagged aliasing or noisy texture, warm saturated hand-painted color palette, in the style of a modern 2D adventure game's key art. Wide landscape composition of a forested river valley, horizon-line framing, no people, no text, no watermark, no UI elements, no signature.

## Level 1 — 15,000 BCE — The Untouched River

> [style anchor] + A pristine glacial river valley at first light, the water so clear the stone riverbed is visible straight through it, and the shallows are almost solid with silver-flanked salmon and trout, fin to fin, more fish than open water. Steep granite walls draped in moss, old-growth conifers crowding right down to the bank, no trail, no clearing, no sign a human hand has ever touched this place. A glacier or lingering snowfield glows on a distant peak, feeding the current with white meltwater. Soft golden dawn light, mist rising off the pools, absolute wilderness silence. Every edge in the scene reads crisp and clean at full resolution, no blur, no soft mushy detail, no compression artifacts.

## Level 2 — 1066 A.D. — A Different Bend, Still Whole

> [style anchor] + A different bend of the same forested river valley, still lush and healthy, the water still running clean over stone, salmon still moving through the pools in visible numbers — plainly fewer than an impossibly overstuffed river, but still a river teeming with life. The only trace of people: a dugout canoe pulled up and resting on the bank, its wood worn smooth, beside a small cluster of bark-covered dwellings set back from the water — no European-style log cabin, no milled lumber, no metal fittings anywhere in frame. No other structures, no smoke, no clearing beyond the small living area shown. Same warm, unhurried daylight as an older, wilder version of this same place. Clean sharp linework throughout, no jagged or noisy edges.

## Level 3 — 1804 A.D. — First Scars

> [style anchor] + The same river valley now showing its first wounds: a patch of raw stumps where old growth used to stand, a crude wooden sluice box and rocker cradle staked into the near bank, the water beside it gone cloudy and silt-brown where the current used to run clear. Upriver the forest is still intact, but the near ground is trampled and bare. A canvas tent camp with a plain flag sits at a distance across the water, thin smoke rising from a cookfire — the camp is clearly unoccupied, no person visible anywhere in the frame, tents and gear only. The sky has gone flatter and grayer, the light cooler than before — a valley that has stopped being lived-with and started being surveyed, measured, claimed. Crisp clean rendering, no soft or blurry passages, no jagged edges on any structure or tree line.

## Level 4 — 1863 A.D. — Gold Camp

> [style anchor] + A gold-rush mining camp overtaking the riverbank: a network of sluice boxes and a raised wooden flume diverting the current, mud-churned water running the color of rust, and a rough shanty skyline crowding the middle distance — canvas tents, plank-board shacks, a two-story false-front building standing in for a saloon, all thrown up crooked and fast. The hillsides above have been stripped and blasted bare in patches, raw dirt and shattered rock where forest canopy used to be, and what timber remains stands as a field of fresh stumps. Harsh, dusty daylight, a haze of woodsmoke and disturbed earth hanging over everything, no people anywhere in frame — a valley being worked hard and given nothing back. Sharp clean edges on every structure, no jagged linework, no blurry or muddy detail.

## Level 5 — 1927 A.D. — What's Left

> [style anchor] + The same river valley reduced to a wasteland: mile after mile of rounded gray dredge tailings piled in long snaking windrows across what used to be the floodplain, and a massive rust-streaked bucket-line dredge looming in the middle distance, gnawing at the last unworked ground. The river itself is choked to a stagnant, silted trickle threading between the tailing piles, dammed and diverted, utterly empty of fish. The surrounding mountainsides are shorn of forest — crosshatched with logging roads, eroded gullies, and stump fields stretching to the ridgeline, with a concrete dam wall visible far upstream. Flat, bleak overcast light near dusk, a desaturated palette of grays, rust, and mud — the same valley from the very first scene, but with every living thing in it stripped, dammed, or buried. No people anywhere in frame. Clean crisp rendering throughout, properly resolved detail on the dredge machinery, no jagged or noisy edges.

## Design notes carried over from the Firefly pass (still apply)

- **Level 5 deliberately echoes Level 1's composition** (same valley,
  same implied vantage point) — the player should recognize it's the
  *same place*, devastated.
- **Level 2's human trace is a canoe + bark dwellings, explicitly not
  European architecture** — the first Firefly generation put a
  log-cabin-on-stilts in frame here, which read as settler-era for a
  date meant to be pre-contact. This prompt states the correction
  directly instead of hoping the model infers it.
- **Levels 3 and 4 now say "no people anywhere in frame" explicitly.**
  The shipped Level 3 background has a small, barely-visible figure near
  the tent despite the original prompt's general "no people" instruction
  — being specific about *where* a figure would otherwise go (near the
  camp/structures) rather than a single blanket instruction at the top
  seems worth trying this round.

## If results still look jagged after this

In rough order of what to try:
1. Raise steps first (try 36-40) — the cheapest fix if detail is
   genuinely under-resolved rather than a style mismatch.
2. Lower Distilled CFG a little (try 2.5-3.0) if edges look harsh or
   over-crunched rather than soft.
3. Send me a generated image even if you don't love it — "jagged" can
   mean several different specific things (aliasing, over-sharpening,
   genuine low detail, a style mismatch with what cel-shaded linework
   actually looks like at this resolution) and I can diagnose faster
   from a real sample than from a description.
