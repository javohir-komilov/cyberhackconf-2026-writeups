# My Trip

| Field | Value |
|-------|-------|
| Category | OSINT |
| Points | ? |

## Description

> One of my friends traveled from Kokand to Tashkent by car and arrived early in the morning.
> The next day he asked: "Where did I go yesterday?" He posted 3 photos from the places he visited.
> Help me figure out where he went.

**Files:** `src/` (3 images with question hints)

## Solution

### Image 1 — Café (`1_cafe.JPG`)

Use **Google Lens** reverse image search on the photo.

The match is a café called **Cavum** in Tashkent.

**Answer: `cavic`** *(cafe name in Tashkent)*

---

### Image 2 — Game club (`2_game.png`)

**Hint:** Around the Korzinka supermarket that burned on **31.01.2026**.

1. Search for the Korzinka fire incident → identify which branch burned → get its address
2. Search for game clubs near that address on 2GIS/Google Maps
3. The first result is **DarkZone** — check reviews to confirm the photo matches

**Answer: `darkzone`**

---

### Image 3 — Building (`3_building.png`)

**Hint:** "Do not leave out any part of the text. This building is a sales department."

Examine the building signage carefully → **Akfa** group building.

Search for "Akfa sales office Tashkent" → locate the building in 3D view on maps to confirm match.

Check the nearest **metro station**: **Mashinasozlar**

**Answer: `mashinasozlar`**

---

### Flag assembly

```
CHC{answer1_answer2_answer3}
```

## Flag

`CHC{cavic_darkzone_mashinasozlar}`
