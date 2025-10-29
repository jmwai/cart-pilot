# Chatbox Redesign Plan - Sticky Right Side Panel

## Overview
Redesign the shopping assistant chatbox to be a persistent right-side panel that extends from the header to the bottom of the page, similar to the inspiration design. The main content area will be adjusted to accommodate the chatbox without overlap.

## Design Goals
1. **Sticky Right Panel**: Chatbox stays fixed on the right side, always visible
2. **Header Integration**: Chatbox extends to the top (starts at header level)
3. **No Content Overlap**: Product grid shifts left to avoid chatbox
4. **Consistent Layout**: Apply same pattern to landing page and product detail page
5. **Modern Aesthetic**: Clean, spacious design inspired by the reference image

---

## Phase 1: Layout Structure & CSS Foundation

### 1.1 Root Layout Changes (`layout.tsx`)
- Add global CSS variables for chatbox width
- Set up CSS custom properties:
  - `--chatbox-width: 420px` (desktop)
  - `--chatbox-width-mobile: 100vw` (mobile, overlays)

### 1.2 Global CSS Updates (`globals.css`)
- Add layout utilities:
  - `.layout-with-chatbox`: Container for pages with chatbox
  - `.main-content`: Content area with right padding/margin for chatbox
  - `.chatbox-panel`: Sticky right panel styles
- Responsive breakpoints:
  - Desktop (≥1024px): Side-by-side layout
  - Tablet (768px-1023px): Chatbox overlays with backdrop
  - Mobile (<768px): Chatbox overlays full screen

---

## Phase 2: Header Component Updates

### 2.1 Header Layout (`Header.tsx`)
**Current State:**
- Full-width header with logo, nav, and auth buttons
- `max-w-7xl` container

**Changes:**
- Split header into two sections:
  - **Left Section**: Logo, navigation (takes available width minus chatbox)
  - **Right Section**: Auth buttons (positioned to avoid chatbox overlap)
- Update container:
  - Remove `max-w-7xl` from header itself
  - Add inner container with `max-w-[calc(100%-var(--chatbox-width))]` on desktop
  - Position auth buttons to stop before chatbox area
- Desktop: Header width = `calc(100% - var(--chatbox-width))`
- Mobile: Header remains full-width

**Specific Updates:**
```tsx
// Header should be:
- Container: full width but padding accounts for chatbox
- Inner content: max-width calculation prevents overlap
- Sticky positioning: top-0, z-50 (below chatbox z-index)
```

---

## Phase 3: Chatbox Component Redesign

### 3.1 Chatbox Structure (`Chatbox.tsx`)
**Current State:**
- Floating button + modal-style window
- Fixed positioning: `bottom-6 right-6`
- Size: `w-[500px] h-[700px]`

**New Structure:**
- **Always visible** (no floating button needed on desktop)
- **Sticky positioning**: `fixed top-0 right-0 bottom-0`
- **Full height**: `h-screen` or `h-[100vh]`
- **Fixed width**: `w-[420px]` (desktop)
- **Z-index**: `z-50` (above header z-40, content z-10)

### 3.2 Chatbox Styling
**Header Section:**
- Height: ~64px (matches main header)
- Background: `bg-blue-600` (maintains current blue theme)
- Text: `text-white`
- Border-bottom to separate from content
- Title: "Shopping Assistant" or icon + text
- Optional: Character illustration/mascot (can be added later)

**Content Area:**
- Flex container with flex-col
- Messages area: `flex-1 overflow-y-auto`
- Background: `bg-gray-50` (maintains current light gray)
- Input area: Fixed at bottom, border-top, `bg-white`

**Mobile Behavior:**
- Overlay: `fixed inset-0` (full screen)
- Backdrop: Dark overlay with opacity
- Toggle button: Floating button to open/close (`bg-blue-600 hover:bg-blue-700`)
- Slide-in animation from right

### 3.3 Chatbox Visual Design
**Color Scheme (Maintain Current):**
- Header: `bg-blue-600` with `text-white`
- Header icon/avatar: `bg-blue-500`
- Header hover: `hover:bg-blue-700`
- Content background: `bg-gray-50`
- Message bubbles:
  - User: `bg-blue-600 text-white`
  - Assistant: `bg-white text-gray-800 border border-gray-200`
- Input area: `bg-white border-t border-gray-200`
- Send button: `bg-blue-600 hover:bg-blue-700 text-white`
- Borders: `border-gray-200`
- Text colors: `text-gray-900`, `text-gray-800`, `text-gray-600`

**Typography:**
- Consistent with existing design system
- Clear hierarchy for messages vs. metadata

---

## Phase 4: Landing Page Updates (`page.tsx`)

### 4.1 Layout Structure
**Current:**
```tsx
<div className="min-h-screen flex flex-col">
  <Header />
  <main className="flex-1">
    <section className="max-w-7xl mx-auto ...">
      {/* Products Grid */}
    </section>
  </main>
  <Footer />
  <Chatbox />
</div>
```

**New:**
```tsx
<div className="min-h-screen flex flex-col layout-with-chatbox">
  <Header />
  <main className="flex-1 main-content">
    <section className="max-w-[calc(100%-var(--chatbox-width)-2rem)] mx-auto ...">
      {/* Products Grid - adjusted for chatbox */}
    </section>
  </main>
  <Footer />
  <Chatbox />
</div>
```

### 4.2 Product Grid Adjustments
- Remove `max-w-7xl` constraint (or adjust calculation)
- Add right padding: `pr-[var(--chatbox-width)]` on desktop
- Grid layout:
  - Desktop: `grid-cols-3` (reduced from 4 if needed)
  - Spacing remains consistent
  - Cards never overlap chatbox

### 4.3 Footer Updates
- Footer width should match main content
- Right margin/padding accounts for chatbox
- Same `max-w-[calc(...)]` calculation

---

## Phase 5: Product Detail Page Updates (`products/[id]/page.tsx`)

### 5.1 Layout Structure
**Changes:**
- Apply same `layout-with-chatbox` pattern
- Main content container: Adjusted max-width calculation
- Product detail section: Two-column grid accounts for chatbox
- "You Might Also Like" section: Same width constraints

### 5.2 Product Info Layout
- Image + Info grid: Stays two-column but narrower
- Max-width: `max-w-[calc(100%-var(--chatbox-width)-2rem)]`
- Maintains responsive behavior on mobile/tablet

---

## Phase 6: Responsive Design

### 6.1 Desktop (≥1024px)
- Chatbox: Fixed right panel, 420px wide
- Content: Shifts left automatically
- Header: Split layout, accounts for chatbox

### 6.2 Tablet (768px - 1023px)
- Chatbox: Overlays content from right
- Width: ~380px
- Backdrop: Semi-transparent overlay when open
- Toggle: Floating button (bottom-right)
- Header: Full-width (chatbox overlays)

### 6.3 Mobile (<768px)
- Chatbox: Full-screen overlay
- Toggle: Floating button
- Slide-in animation from right
- Header: Full-width
- Content: Full-width (chatbox hidden by default)

---

## Phase 7: State Management & Interactions

### 7.1 Chatbox Visibility
- Desktop: Always visible (no toggle needed)
- Tablet/Mobile: Toggle state (`isOpen`)
- Persist state: Use localStorage if desired

### 7.2 Scroll Behavior
- Chatbox: Independent scroll (messages area)
- Main content: Normal scroll
- No interference between scrolls

### 7.3 Focus Management
- When chatbox opens on mobile: Focus input field
- When closing: Return focus to trigger button

---

## Phase 8: Visual Polish

### 8.1 Transitions & Animations
- Mobile: Slide-in from right (300ms ease)
- Desktop: Smooth layout shift when resizing
- Button hover states
- Message appearance animations

### 8.2 Typography & Spacing
- Consistent spacing throughout
- Message bubbles: Clear separation
- Product cards: Adequate padding

### 8.3 Additional Elements (Future)
- Character illustration in chatbox header
- "Listening..." indicator (animated)
- Visual feedback for cart updates
- Typing indicators

---

## Implementation Order

1. **Phase 1**: CSS Foundation & Layout Utilities
2. **Phase 2**: Header Component Updates
3. **Phase 3**: Chatbox Component Redesign (Structure)
4. **Phase 4**: Landing Page Layout Updates
5. **Phase 5**: Product Detail Page Updates
6. **Phase 6**: Responsive Behavior
7. **Phase 7**: State & Interactions
8. **Phase 8**: Visual Polish

---

## Technical Considerations

### CSS Variables
```css
:root {
  --chatbox-width: 420px;
  --chatbox-width-tablet: 380px;
  --header-height: 64px;
  --content-padding: 1rem;
}
```

### Z-Index Hierarchy
- Header: `z-40`
- Chatbox: `z-50`
- Mobile overlay backdrop: `z-45`
- Product cards: `z-10`

### Performance
- Use CSS transforms for animations (GPU-accelerated)
- Lazy load chatbox content if needed
- Optimize product grid rendering

### Accessibility
- ARIA labels for chatbox toggle
- Keyboard navigation support
- Focus management
- Screen reader announcements

---

## Success Criteria

1. ✅ Chatbox is sticky on right side, extends from header to bottom
2. ✅ Product grid never overlaps chatbox
3. ✅ Header layout accounts for chatbox width
4. ✅ Responsive: Works on mobile, tablet, desktop
5. ✅ Consistent layout on landing page and product detail page
6. ✅ Smooth transitions and interactions
7. ✅ Maintains existing functionality (products, cart, chat)

---

## Notes

- Chatbox width (420px) can be adjusted based on testing
- **Color scheme is maintained**: Blue (`bg-blue-600`), white (`bg-white`), and gray (`bg-gray-50`, `border-gray-200`) theme continues
- Character illustration can be added in a future iteration
- Consider adding a minimize/maximize feature for desktop in future

