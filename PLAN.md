# Edit Search Flow Implementation Plan

## Overview
Add the ability for users to refine their search after seeing initial results, without having to start over from the beginning. This includes a collapsible "Edit search" panel on the results page.

## Screenshots Reference
- 1.webp: Initial search form
- 2.webp: Results with "Your Search" section showing query + categories
- 3.webp: Results with "Edit search" collapsible button (collapsed)
- 4.webp: Results without edit (earlier state)
- 5.webp: Edit panel expanded with form fields
- 6.webp: Full view with edit panel expanded, Update Search/Cancel buttons
- 7.webp: Final results with edit collapsed
- 8.webp: Streaming results state

## Implementation Steps

### Step 1: Create RefinePromptPanel Component
**File:** `frontend/src/components/RefinePromptPanel.tsx`

Create a new collapsible panel component with:
- **Collapsed state:** Shows "✏️ Edit search" button with chevron
- **Expanded state:** Shows "✏️ Editing search" header with upward chevron
- **Form fields when expanded:**
  - Client description (textarea)
  - Location (optional) (input)
  - Resource categories (optional) - toggle buttons grid
  - Provider types (optional) - toggle buttons
- **Action buttons:** "Update Search" (primary) and "Cancel" (secondary)
- **Loading state:** "Updating search..." with spinner, buttons disabled
- **Unsaved changes indicator:** Amber text when form differs from original values

**Props interface:**
```typescript
interface RefinePromptPanelProps {
  clientDescription: string;
  locationText: string;
  selectedCategories: string[];
  selectedResourceTypes: string[];
  isLoading: boolean;
  onRefine: (
    newClientDescription: string,
    newLocationText: string,
    newSelectedCategories: string[],
    newSelectedResourceTypes: string[]
  ) => void;
}
```

### Step 2: Update ClientDetailsPromptBubble Component
**File:** `frontend/src/components/ClientDetailsPromptBubble.tsx`

Modify to:
- Add "Your Search" section header above the prompt bubble
- Display the user's query in quotes with bold styling
- Show categories and location as metadata below the query (e.g., "Categories: Food Assistance")
- Accept additional props for categories and location

**Updated props:**
```typescript
interface ClientDetailsPromptBubbleProps {
  clientDescription: string;
  selectedCategories?: string[];
  locationText?: string;
}
```

### Step 3: Update page.tsx
**File:** `frontend/src/app/[locale]/generate-referrals/page.tsx`

Changes needed:

1. **Add new state:**
   - Track original search values for comparison (to detect unsaved changes)

2. **Add handleRefineSearch function:**
   ```typescript
   function handleRefineSearch(
     newClientDescription: string,
     newLocationText: string,
     newSelectedCategories: string[],
     newSelectedResourceTypes: string[]
   ) {
     // Update state with new values
     setClientDescription(newClientDescription);
     setLocationText(newLocationText);
     setSelectedCategories(newSelectedCategories);
     setSelectedResourceTypes(newSelectedResourceTypes);

     // Clear previous results and action plan
     setRetainedResources(undefined);
     setSelectedResources([]);
     setActionPlan(null);
     setStreamingPlan(null);
     setActionPlanResultId("");

     // Trigger new search
     void findResources();
   }
   ```

3. **Modify findResources to accept overrides:**
   - Allow passing overrides for the search parameters since setState is async

4. **Update JSX structure:**
   - Add "Your Search" header section
   - Position RefinePromptPanel between the search summary and resources
   - Update ClientDetailsPromptBubble to show categories/location

### Step 4: Add "Resources" Section Header
Add a "Resources" heading above the ResourcesList component for visual structure.

### Step 5: Handle Loading States
- Disable Edit search button while resources are streaming
- Show "Updating search..." in the panel during refine
- Disable Print/Email buttons during search

## Component Hierarchy (Results View)

```
<div> (results container)
  ├── Header row (Return To Search, Print/Email)
  ├── "Your Search" section
  │   └── <ClientDetailsPromptBubble />
  ├── <RefinePromptPanel /> (collapsible)
  ├── "Resources" heading
  └── <ResourcesList />
  └── <ActionPlanSection />
  └── Share footer
</div>
```

## UI/UX Details

### Collapsed State
- Blue rounded border container
- "✏️ Edit search" text in blue
- Chevron pointing down on right

### Expanded State
- Light blue/gray background header
- "✏️ Editing search" text
- Chevron pointing up
- White form area below with:
  - Client description label + textarea
  - Location (optional) label + input
  - Resource categories (optional) label + button grid
  - Provider types (optional) label + button row
  - Update Search (blue) + Cancel (outline) buttons

### Loading State
- Panel shows "Updating search..." with spinner
- Update Search and Cancel buttons disabled
- Edit search button hidden/disabled

### Unsaved Changes
- Amber colored "Unsaved changes" text appears
- Shown when form values differ from last search values

## Testing Checklist
- [ ] Initial search works as before
- [ ] Edit search panel expands/collapses correctly
- [ ] Form fields pre-populate with current search values
- [ ] Unsaved changes indicator appears when values change
- [ ] Cancel reverts form to original values and collapses
- [ ] Update Search triggers new search with updated values
- [ ] Previous results clear when new search starts
- [ ] Streaming works correctly for refined searches
- [ ] Loading states display correctly
- [ ] Print/Email disabled during search
- [ ] Return To Search still works
