# Aurelia — The Floating Isles

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/OhhRayy/poster-place-20261121/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/OhhRayy/poster-place-20261121/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

Entry for the make.fun bounty
[The Poster for a Place That Isn't There](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539):
a travel poster for a place that does not exist.

## What the poster shows

**Aurelia, the Floating Isles** — a chain of green-topped islands
drifting above a sea of clouds at golden hour. The largest island
carries a striped lighthouse whose beam sweeps the evening sky, a
waterfall spills off its edge into the clouds below, and a low sun
hangs over the horizon while the first stars come out. The place's
name is set large across the sky, with one honest tagline:
"Above the clouds, beyond the map."

## How it works

The image itself is `entry.png` in this repository. The entrypoint,
`main.py` (Python 3.13, standard library plus Pillow), draws the
poster procedurally from a fixed seed — sky gradient, sun, cloud
sea, floating islands, lighthouse, birds and type — and writes it
to the directory named by `MAKEFUN_OUTPUT_DIR` (default `/output`)
as `entry.png`. It then checks the result: 1024 by 1024 pixels and
no more than 1,048,576 bytes, raising a `RuntimeError` if either
check fails. It reads no network, and two runs produce
byte-identical output.

The fonts the poster uses ship in this repository under `assets/`,
so the drawing does not depend on the fonts a machine happens to
have. If Pillow is missing where the program runs, it falls back to
the copy of the poster that ships here as `entry.png` and verifies
that copy the same way.

Run it locally with:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Verified locally: two runs into separate directories produced
byte-identical copies of entry.png (matching SHA-256 hashes),
261,245 bytes, 1024 by 1024 pixels.
