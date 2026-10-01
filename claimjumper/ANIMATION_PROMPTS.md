# CLAIMJUMPER — v7.3+ Animation Prompts (revision pass)

Firefly video-generation prompts for a follow-up pass on the five miner
skins plus the player, aimed squarely at the technical problems the v7.3
extraction pipeline actually hit pulling usable frames out of
`CLAIMJUMPER_NEW_ASSETS_OCT_2026.zip`. The art itself (the character
designs, the painterly cel-shaded illustration style) worked and should
stay — nothing here asks for a different look. Every requirement below
exists because it maps to a concrete bug that shipped, got reported, or
had to be papered over with extraction tricks (positional cutoffs,
dock-merge masking, a flip after the fact). Think of this as "the same
clips, filmed so the extraction step doesn't have to fight the footage."

All six open with the same style anchor, kept word-for-word, so a new
pass reads as the same character set rather than six unrelated clips.

## Style anchor (opens every prompt below)

> Painterly 2D video game character illustration, clean bold linework, saturated color, soft cel-shading with directional light, dynamic action pose, game-sprite illustration style. 8-second video clip, 24fps, static locked-off camera with no pan, zoom, dolly, or handheld movement — the character is the only thing that moves in frame. Plain, flat, minimal ground with no deck, dock, pier, or wooden platform under the character's feet. Transparent background rendered as a plain neutral gray-and-white checkerboard with no color tint, gradient, vignette, or lighting cast over it.

## Universal requirements (why each one is here)

These apply to every clip below, not just the ones called out by name —
each is a lesson from a real extraction bug in the current set:

1. **Facing direction is load-bearing, not cosmetic.** State it explicitly
   every time: the five miners face and move toward **screen left** (they
   walk in from the right, toward the player's side); the player faces
   **screen right** (he throws across the water, the opposite way). Archer
   shipped facing backward because this was never pinned down in the
   original prompt and the clip happened to face the wrong way — the only
   one of five that did, confirming it's pure luck otherwise, not a given.
2. **Include a real neutral idle, held for a full second or more**, before
   anything else happens — weapon down or at rest, no wind-up tension in
   the pose. Two of the five source clips (archer, and the player's own
   action clip) never actually contained this, forcing a same-pose
   placeholder reused from mid-sequence instead of a true idle.
3. **The thrown object must separate from the hand clean** — once it
   leaves, no glow, light aura, motion-blur trail, or speed-lines baked
   onto it. The game draws its own projectile and its own motion effect
   separately once the real object is in flight; anything pre-baked here
   either has to be surgically cut out in post (costly, lossy, sometimes
   impossible) or ships as a visual duplicate. This was the single
   largest source of extraction work across the whole set — rockthrower's
   rock, archer's arrow, and the player's spear all separated cleanly;
   the soldier's bottle needed real work; prospector's thrown nugget
   never fully separated and still ships with a known, visible fingertip
   casualty from the cutoff used to contain it.
4. **No platform under the character**, full stop, unless the character's
   own fiction strictly requires standing on something (the player's
   fishing tower). A wooden deck/dock/plank under the feet repeatedly
   fused with the character during background removal, since both read as
   similarly warm-toned opaque pixels to a simple color-based cutout —
   this cost real extraction effort on three of the five clips (soldier,
   archer, and the player's own throw clip) and is trivially avoidable by
   just not filming it. If a platform is unavoidable, ask explicitly for
   a single flat, uniformly-colored surface with a hard, high-contrast
   top edge, distinctly different in color from the character's own
   palette.
5. **Distinct, held phases** — ready/idle, wind-up, release, recovery —
   each lasting at least half a second with a clear held pose at its
   peak, rather than one continuous blurred-through motion. This is what
   makes picking clean individual frames afterward reliable instead of
   guesswork.
6. **A genuinely plain checkerboard**, not a checkerboard pattern with
   color grading, ambient tint, or soft lighting painted over it. Every
   single clip in the current set had some version of this problem (the
   whole reason the extraction pipeline needs a "is this background"
   color-tolerance check at all, rather than a flat alpha key) — it's
   worth over-specifying since it was never fully clean even once.

## Rockthrower

> [style anchor] + A muscular warrior in red ochre body paint and a dark feathered headdress, standing in a wide athletic throwing stance facing screen left. Idle: standing relaxed, a stone held loosely at his hip in a small pouch, weight settled, no tension. Wind-up: he draws the stone back and up past his shoulder in a clear two-stage motion, torso coiling. Release: a sharp forward throwing motion, arm snapping fully extended toward screen left exactly as the stone leaves his hand — his hand is empty immediately after, no residual stone, no motion trail on the thrown stone itself. Recovery: he settles back down into the idle stance over about a second.

*Worked best of the five as filmed — standalone, no dock, no baked
projectile trail — kept close to the original brief rather than changed.*

## Soldier

> [style anchor] + A grizzled cavalry-coated frontier soldier with a rifle slung on his back, standing in a wide stance facing screen left, a glass bottle in his throwing hand. Idle: standing at ease, bottle held low and relaxed. Wind-up: he raises the bottle back past his shoulder, coiling to throw, over about a second. Release: a full-body throwing motion, arm snapping forward toward screen left exactly as the bottle leaves his hand — empty hand immediately after, no residual bottle or glass shards trailing it. Recovery: he settles back to the idle stance. Also include a walking cycle: a full stride cycle of him walking toward screen left, arms swinging naturally, on the same plain ground as the rest of the clip.

*Last pass needed `body_only_above` masking to separate him from a dock
his feet were standing on — asking for plain ground up front removes
that step entirely.*

## Prospector

> [style anchor] + A grizzled prospector in a canvas jacket and mining helmet, a lit headlamp on his hat, standing facing screen left, a raw gold nugget held in his throwing hand. Idle: standing relaxed, examining the nugget, headlamp lit but casting no visible glow or light beam in the shot. Wind-up: he draws the nugget back past his shoulder. Release: a full throwing motion toward screen left, the nugget leaving his hand cleanly — no glow, no light trail, no lens flare, no particle sparkle on the nugget either before or after release, just a plain solid thrown object. Recovery: he settles back to idle, pointing after the throw. Also include a walking cycle: a full stride cycle walking toward screen left, a lantern swinging from his belt, no light-glow or halo effect around the lit lantern.

*The one clip where "no motion trail" wasn't enough context — the
previous prompt's lit headlamp/lantern produced a soft ambient glow that
stayed fused to his body as one continuous shape with no seam to cut
along, through the whole wind-up, release, and walk cycle. This prompt
asks for the lit props without their light-glow rendered, which should
remove the problem at the source instead of needing a positional
workaround to contain it the way the current set does.*

## Archer

> [style anchor] + A warrior in a feathered headdress with a quiver on his back, standing in an archery stance facing screen left, bow held in his left hand with the string drawn toward screen right. Idle: standing relaxed, bow lowered and undrawn, arrow not yet nocked — a genuine at-ease pose, held for a full second or more before anything else happens. Wind-up: he nocks an arrow and draws the bowstring back toward screen right over about a second, reaching full draw. Release: the string snaps forward, the arrow fires toward screen left and immediately separates from the bow — no motion trail or speed-lines on the arrow once it's away. Recovery: the bow relaxes and he settles back toward the idle stance. Also include a walking cycle: a full stride cycle of him walking toward screen left on the same plain ground, quiver and headdress feathers moving naturally.

*Two fixes baked in here: he shipped facing screen right in the current
set (confirmed backward — the only one of five, and it was never caught
until it was live), and the current clip never shows a genuine undrawn
idle at all, so the shipped "stand" pose is actually a recovery frame
doing double duty. Both are called out explicitly this time instead of
left implicit.*

## Player

> [style anchor] + A young river fisherman with a long trident-tipped fishing spear, standing on a plain wooden fishing platform (flat, single-tone planking, no net or rigging cluttering the silhouette) facing screen right. Idle: standing relaxed, spear held low and forward, weight settled, waiting. Wind-up: he raises the spear back and up past his shoulder in a clear two-stage motion, torso coiling, building toward a full overhead cock. Release: a full lunging thrust toward screen right, arm fully extended, the spear leaving his hand completely — empty hand immediately after, no residual spear, no motion trail. Recovery: a fresh spear is already back in his re-gripped hand as his arm lowers back toward the idle stance over about a second. Film this full idle/wind-up/release/recovery sequence three times at three different throwing angles: once thrown nearly level (barely angled down), once at a clear 45-degree downward angle, and once thrown steeply down near-vertical into the water at his feet.

*This is the one real ask beyond "fix the extraction problems": the
current clip only covers a single ~8-degree throwing angle, but the
game aims continuously from 8 to 88 degrees. The current build covers
that gap with a rotation correction capped at +-20 degrees — close to
convincing near the shallow end this one clip provides, visibly
approximate at the steep end. Three angles (shallow, mid, steep) instead
of one would let the in-game system pick the nearest real filmed pose
per aim angle the same way the six existing idle-bucket poses already
do, instead of rotating one pose across the whole range. If only one
angle is practical to shoot, keep it near the shallow end (closest to
`figure_up_soft`/`figure_level`) since that's what the current approximation
already covers best — but three is a real improvement, not a nice-to-have.*

## Design notes

- **The checkerboard-as-fake-transparency problem is universal and worth
  solving once**, not per-clip — if there's any way to request a true
  alpha channel (a format Firefly actually exports with real
  transparency, rather than a checkerboard pattern standing in for it),
  that removes an entire pipeline step and its failure modes at once.
  Everything else in this document is written assuming that's not
  available and the checkerboard convention stays.
- **Every "no motion trail / no glow" instruction exists because the
  game already draws its own projectile and its own flight effects
  separately** (`drawSpear()`, `G.rocks`, per-skin trail rendering in
  `drawPlay()`) once an object leaves a character's hand. Anything baked
  into the source footage after that point is pure downside: it can't be
  turned off, and at best it's redundant with what the game already
  renders, at worst it visibly doubles up or has to be cut out by hand.
- **Consider requesting a few static reference stills alongside the
  video clips** — a clean idle pose, a clean full-wind-up pose, and a
  clean release pose, each as a plain still image rather than extracted
  from video. Every quality issue the current set has (codec noise,
  motion blur between poses, the checkerboard tint drifting frame to
  frame) comes from pulling frames out of compressed video; a still
  image doesn't have any of those problems and would make the "idle" and
  "full wind-up" keyframes in particular much cleaner, since those are
  exactly the two moments every clip needs held motionless anyway.
- **Not addressed here**: the recurring small print-through where bright
  near-white details (an eye-white, a hat spark, a glare highlight) get
  misread as background by the same color-tolerance test that reads the
  checkerboard. It's never been visible at actual in-game sprite scale
  (sub-pixel after the ~0.4x downscale every asset gets), so it isn't
  worth a prompt change — flagged here only so it isn't mistaken for a
  gap if someone goes looking for it later.
