# Recording the demo GIFs

`docs/index.html` ships with real, reproducible **static** transcripts, so it works
with no GIFs at all. To add the animated demos, drop three files into
`docs/assets/gifs/`:

| file | shows | prompt to record |
|---|---|---|
| `quick.gif` | Tier-0 cited lookup | `/quick most massive black hole merger so far` |
| `init.gif` | first-run priming | `/init lvk` (then `/quick largest GWB amplitude so far` after `/praxis-use pta`) |
| `investigate.gif` | the full loop | `/investigate Is GW190814's secondary a neutron star or a black hole?` |

The `<img>` slots auto-hide and show a labeled placeholder when a GIF is absent, so
you can add them one at a time.

## Option A — `vhs` (deterministic, no manual screen-recording)

[charmbracelet/vhs](https://github.com/charmbracelet/vhs) renders a `.tape` script to a GIF.

```bash
brew install vhs
# example tape:
cat > quick.tape <<'TAPE'
Output docs/assets/gifs/quick.gif
Set FontSize 20
Set Width 1100
Set Height 480
Type "claude"   Enter   Sleep 2s
Type "/quick most massive black hole merger so far"   Enter   Sleep 8s
TAPE
vhs quick.tape
```

## Option B — `asciinema` → `agg`

```bash
brew install asciinema agg
asciinema rec quick.cast          # run the prompt, Ctrl-D to stop
agg quick.cast docs/assets/gifs/quick.gif
```

## Option C — ask me to generate self-contained animated SVG mockups

If you'd rather not record live sessions, I can generate animated **SVG** "typed
terminal" mockups from the exact real transcripts already embedded in
`index.html` — self-contained, versionable, no binary assets. Say the word and I
will swap the GIF slots for inline SVGs.

Keep recordings short (< 15 s) and crop to the terminal. Commit the GIFs under
`docs/assets/gifs/`; GitHub Pages serves them from the same directory.
