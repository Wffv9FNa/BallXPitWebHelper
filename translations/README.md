# Translation Files

This directory contains translation files for the Ball X Pit Helper app.

## File Structure

### `zh-CN.json` - Simplified Chinese Translations

This file contains all Chinese translations for the app. It covers **every** ball
and passive in `data/` - 90 balls and 71 passives as of 2026-09-12.

**Verification Status:**

The `verified` flag describes the **name only**.

- ✅ = **Verified** - the Chinese name is byte-identical to a string in the game's
  own localisation table (`Balls_Data/resources.assets`), checked 2026-09-12.
- ⚠️ = **Needs Verification** - not found in that table.

All 161 entries are currently ✅.

This is a stricter standard than the one this file used before. The previous ✅
meant "found in an official Steam or community guide", which turned out to be
unreliable: ten names disagreed with the game - and seven of those ten were
marked ✅. None of the ten appear anywhere in the game's strings. Those guides
contain their authors' own translations, not the shipped strings. **Do not re-mark an entry ✅ on the strength of a guide.** Only the game
itself counts.

**Descriptions are not covered by the flag.** They are unverified community
translations inherited from earlier work. An entry whose `description` is `""`
falls back to the English text from `data/balls.ts` or `data/passives.ts`
(see `getBallDescription` in `lib/i18n/useTranslation.ts`), which is why leaving
it empty is preferable to guessing.

## How to Review and Edit

### 1. Open the file

Open `zh-CN.json` in any text editor (VS Code, Notepad++, etc.)

### 2. Review translations

Names are settled. The open work is **descriptions**: 82 of 161 entries still
have an empty one and fall back to English.

### 3. Edit translations

Change the Chinese text, leaving `verified` alone unless you have checked the
name against the game itself. For example:

**Before:**

```json
"ghost": {
  "name": "幽灵",
  "description": "",
  "verified": "✅"
}
```

**After (adding a description):**

```json
"ghost": {
  "name": "幽灵",
  "description": "穿过敌人",
  "verified": "✅"
}
```

### 4. Where the names came from

The game ships a localisation table inside `Balls_Data/resources.assets` in the
install directory, holding every UI string keyed by internal ID
(`landslide_name`, `landslide_desc`, ...) across at least seven languages. Those
internal IDs line up 1:1 with this project's IDs. Both the Chinese and English
names in this file were confirmed present there, 161/161.

That table also holds Chinese **descriptions**, but they arrive with unresolved
`{[placeholder]}` tokens (`每次反弹使弹珠的速度提高{[acceleration]}`) rather than
concrete numbers, so they were not imported. Resolving them is the natural next
step for filling the 82 empty descriptions.

## JSON Format Tips

- Keep the structure intact (don't remove quotes or commas)
- Chinese text should be inside double quotes: `"name": "中文名字"`
- Each entry ends with a comma except the last one in a section
- Use a JSON validator if you want to check for syntax errors

## Finding Ball IDs

Ball IDs in the JSON match the image filenames in `/public/balls/`:

- `bleed.png` → `"bleed"`
- `frost-ray.png` → `"frost-ray"`
- `black-hole.png` → `"black-hole"`

Entry order matches `data/balls.ts` and `data/passives.ts`, so the two read
side by side.

## Other files here

`chinese-translations.md`, `discrepancies-report.md` and `steam-guide-mapping.md`
are superseded working notes from the Steam-guide sourcing effort. Their ✅/⚠️
marks predate the in-game verification and should not be trusted.
