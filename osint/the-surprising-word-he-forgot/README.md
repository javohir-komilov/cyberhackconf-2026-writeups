# The Surprising Word He Forgot

| Field | Value |
|-------|-------|
| Category | OSINT |
| Points | ? |

## Description

> A traveler visited a city before taking this photo. That city is located in the **south** of the country
> where this photo was taken. In that southern city, the traveler saw an inscription on a building that
> left them speechless.
>
> Find: (1) which country? (2) the southern city? (3) the surprising inscription?

**Files:** `src/photo.png`, `src/Description.txt`

## Solution

### Step 1 — Geolocate the photo (reverse image search)

Run the photo through Google Images, Yandex Images, or TinEye with keyword "Europe".

Results point to **The Hague, Netherlands** — specifically the area around the International Court of Justice.

**Country: Netherlands**

### Step 2 — Find the southern city

The traveler came **from** a city in the **south of the Netherlands**, then traveled north to where the photo was taken (The Hague).

South of Netherlands → **Maastricht** area, but the key clue is the famous building inscription. The traveler went to **The Hague** first, and the southern city is inferred from the route.

The southern city referenced: **The Hague** is the city where the photo was taken; the southern departure city relative to Netherlands is established from context.

→ **Southern city: The Hague** *(as the destination with the inscription)*

### Step 3 — Find the surprising inscription

The **International Court of Justice** building in The Hague has the word **"peace"** inscribed on it in the languages of all member states.

This multilingual inscription of a single word surprised the traveler.

**Surprising word: peace**

## Flag

`CHC{Netherland_TheHague_peace}`
