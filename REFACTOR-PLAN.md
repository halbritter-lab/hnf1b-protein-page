# Refactor Plan: Modular HNF1B Protein Viewer

## Target Structure
```
hnf1b-protein-viewer/
├── index.html
├── css/
│   ├── main.css          # Global styles and layout
│   ├── viewer.css        # 3D viewer styles
│   └── variants.css      # Variant list and UI styles
└── js/
    ├── variants.js       # Variant data
    ├── ProteinViewer.js  # NGL viewer management
    ├── VariantManager.js # Variant UI logic
    └── main.js           # App initialization
```

## Implementation Steps

### Step 1: Extract CSS
- Split embedded styles into 3 CSS files
- Link CSS files in HTML head
- Keep exact same styling

### Step 2: Extract JavaScript
- **ProteinViewer.js**: NGL.js wrapper, protein loading/rendering
- **VariantManager.js**: Variant data handling, DOM manipulation, events  
- **variants.js**: Move variant data array to separate file
- **main.js**: Application initialization and coordination

### Step 3: Create Clean HTML
- Remove embedded `<style>` and `<script>` tags
- Add CSS and JS file references
- Keep same HTML structure

## Key Benefits
- **Maintainability**: Separate files for HTML, CSS, JS
- **Readability**: Focused files instead of 200+ line monolith
- **Reusability**: Modular components

## Migration Strategy
1. Create new file structure alongside existing HTML
2. Test functionality matches exactly
3. Replace when ready