# Watch Community Platform — Modern UI Implementation Prompt

## ROLE
You are a senior Product Designer + Frontend Engineer.

Your task is to design and implement a **modern, user-friendly UI** for a Watch Community Platform web application.

The result must feel like a real premium product — clean, minimal, and highly usable.

---

# 0. Design Goals (Strict)

- Minimal, modern, premium aesthetic
- Clean typography with generous whitespace
- Plain, readable fonts (Inter or system font stack)
- No heavy gradients, no flashy colors, no noisy backgrounds
- Consistent 8px spacing system
- Fully responsive (mobile-first)
- Fast, intuitive navigation
- Looks production-ready, not a demo

---

# 1. Tech Stack (Required)

- Next.js 14 (App Router)
- Tailwind CSS
- TanStack Query
- shadcn/ui for UI primitives
- lucide-react for icons

Do not use additional UI frameworks unless absolutely necessary.

---

# 2. Pages To Build

## A) Landing / Home (`/`)

Purpose: Immediate usability + search + trending watches.

Sections:
- Top navigation bar:
  - Logo (left)
  - Search input (center)
  - Upload button
  - Authentication button
- Hero section:
  - Short title
  - Short subtitle
- Large search bar
- Trending / Popular watches grid (8–12 cards)
- Minimal footer

---

## B) Watch List (`/watches`)

Purpose: Browsing with fast filters.

Include:
- Filter sidebar (collapsible on mobile):
  - Brand (select)
  - Dial color (select)
  - Bracelet material (select)
  - Movement type (optional)
- Sort dropdown:
  - Most popular
  - Newest
  - Highest match confidence
- Watch cards showing:
  - Image
  - Brand + Model name
  - 2–3 key specs (diameter, water resistance, movement)
  - Status badge (official / community / ai / disputed / unknown)
- Pagination or infinite scroll

---

## C) Watch Detail (`/watches/[id]`)

Purpose: Display full watch data + community interaction.

Include:
- Image gallery (main image + thumbnails)
- Title: Brand + Model
- Status badges:
  - Official
  - Community Verified
  - AI Estimated
  - Disputed
  - Unknown
- Key specs grid:
  - Case diameter (mm)
  - Water resistance (ATM)
  - Case material
  - Bracelet material
  - Dial color
  - Movement type
  - Weight (g)
  - Crystal type
- Confidence panel:
  - Shows source priority (official/community/ai/disputed)
- Comments section:
  - List of comments
  - Add comment (auth required)
- “Contribute spec correction” button:
  - Opens modal form
  - Allows user to submit corrected spec + evidence (URL or image)
- Community voting UI (confirm / reject)

---

## D) AI Upload / Identify (`/upload`)

Purpose: Upload watch photo and identify.

Include:
- Drag & drop upload area
- Image preview
- “Identify watch” button
- Results section:
  - Top 5 candidates with similarity score bar
  - VLM extracted attributes:
    - brand_guess
    - dial_color
    - bracelet_material
  - Final status: matched / unknown
- If unknown:
  - “Add this watch to database” flow
    - Brand field
    - Model field
    - Optional product URL
    - Submit button

---

## E) Profile (`/me`) (Optional)

Include:
- User contributions
- Votes cast
- Saved watches

---

# 3. Reusable UI Components

Create inside `/components`:

- Navbar.tsx
- WatchCard.tsx
- SpecGrid.tsx
- SpecBadge.tsx
- SearchBar.tsx
- FiltersPanel.tsx
- ImageGallery.tsx
- CommentsList.tsx
- ContributionModal.tsx
- VoteButtons.tsx
- SimilarityBar.tsx
- EmptyState.tsx
- LoadingSkeletons.tsx

---

# 4. Visual Rules (Strict)

Typography:
- Main titles: text-3xl / text-4xl
- Body: text-sm / text-base
- Labels: text-xs

Color system:
- Background: white / gray-50
- Text: gray-900
- Borders: gray-200

Rounded corners:
- rounded-2xl for cards and buttons

Shadows:
- shadow-sm only

Spacing:
- p-4 or p-6 for cards
- gap-4 or gap-6 for layouts

Buttons:
- Primary: solid dark
- Secondary: outline

Accessibility:
- Proper contrast
- Focus states
- Keyboard navigable

---

# 5. UX Requirements

- Loading skeletons everywhere needed
- Proper empty states
- Clean error alerts
- Toast notifications for:
  - Comment posted
  - Contribution submitted
  - Vote submitted
  - Identification completed
- Optimistic UI for voting (optional)

---

# 6. Data Integration

First:
- Use mock data objects

Then:
- Connect to real API endpoints:
  - GET /watches
  - GET /watches/:id
  - GET /watches/:id/specs
  - GET/POST /watches/:id/comments
  - POST /watches/:id/contributions
  - POST /contributions/:id/vote
  - POST /ai/identify

Use TanStack Query.
Keep API logic in `/lib/api.ts`.

---

# 7. Deliverables

1. Full Next.js frontend inside `apps/web`
2. Clean page routing structure
3. Reusable components
4. Fully responsive design
5. Works with mock data
6. Easily switchable to real API

---

# 8. Quality Standard

The result must:
- Feel like a real consumer product
- Have Apple-like cleanliness
- Reflect a premium watch community
- Avoid template-like appearance
- Look polished even with placeholder data

Generate the complete UI implementation.
