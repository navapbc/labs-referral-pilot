# Frontend Styling Cleanup Plan

## Goal
Standardize inconsistent styling patterns so the codebase is easier to maintain and adapt for different organizations/scenarios.

---

## 1. Remove `!important` hex overrides in globals.css

The `.generate-referrals-button` class uses hardcoded `#2563eb !important` instead of CSS variables. Replace with `bg-blue-600` or `hsl(var(--primary))` so it respects the theming system.

**File:** `globals.css` (lines ~130-142)

---

## 2. Standardize secondary text color

Components inconsistently use `text-gray-500` vs `text-gray-600` for secondary/helper text:

| File | Current | Line context |
|------|---------|-------------|
| `ClientDetailsInput.tsx` | `text-gray-600` | Section descriptions |
| `ClientDetailsInput.tsx` | `text-gray-500` | "Optional - select categories" |
| `RefinePromptPanel.tsx` | `text-gray-600` | Metadata labels |

**Decision:** Standardize on `text-gray-600` (better contrast, safer for WCAG AA).

---

## 3. Standardize error text color

- `WelcomeUserInputScreen.tsx` uses `text-red-600`
- `EmailReferralsButton.tsx` uses `text-red-500`

**Decision:** Standardize on `text-red-600` (consistent, better contrast).

---

## 4. Audit and fix `text-gray-400` usage

`text-gray-400` on white may fail WCAG AA 4.5:1 contrast. Find all instances and bump to `text-gray-500` minimum. Likely in disabled/placeholder states.

---

## 5. Extract shared color constants for referral types

Resource cards use a color mapping (goodwill=blue, government=gray, external=green) defined inline in `ResourcesList.tsx`. Extract to a shared config so `CompactResourceList` and any future components use the same values:

```typescript
// src/config/referralTypeColors.ts
export const referralTypeColors = {
  goodwill: { border: "border-t-blue-600", badge: "text-blue-800", bg: "bg-blue-600" },
  government: { border: "border-t-gray-600", badge: "text-gray-800", bg: "bg-gray-600" },
  external: { border: "border-t-green-600", badge: "text-green-800", bg: "bg-green-600" },
};
```

---

## 6. Wire `ScenarioConfig.primaryColor` to CSS variables

The `primaryColor` field exists on every scenario but is unused. Create a lightweight `ThemeProvider` that maps scenario primary color to `--primary` CSS variable, so the entire app rebrands by changing the scenario config.

---

## Summary

| # | Change | Files touched | Effort |
|---|--------|--------------|--------|
| 1 | Remove `!important` hex overrides | `globals.css` | 5 min |
| 2 | Standardize secondary text to `text-gray-600` | 3-4 components | 15 min |
| 3 | Standardize error text to `text-red-600` | 2 components | 5 min |
| 4 | Fix `text-gray-400` contrast | Audit needed | 15 min |
| 5 | Extract referral type color config | `ResourcesList.tsx` + new file | 20 min |
| 6 | Wire primaryColor to CSS variables | New `ThemeProvider` + layout | 30 min |
