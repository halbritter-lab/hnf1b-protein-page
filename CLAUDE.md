# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular bioinformatics visualization tool that displays genetic variants on a 3D protein structure of HNF1B (PDB ID: 2H8R). The application uses the NGL.js library to render 3D molecular visualizations in the browser and is organized into separate HTML, CSS, and JavaScript files for improved maintainability.

## Architecture

**Modular Structure**: The application is organized into separate HTML, CSS, and JavaScript files for maintainability.

**File Structure**:
```
├── index.html              # Main HTML entry point
├── css/
│   ├── main.css           # Global styles and layout
│   ├── viewer.css         # 3D viewer container styles
│   └── variants.css       # Variant list and UI styles
└── js/
    ├── variants.js        # Variant data configuration
    ├── ProteinViewer.js   # NGL viewer management class
    ├── VariantManager.js  # Variant UI logic class
    └── main.js            # Application initialization
```

**Core Components**:
- **ProteinViewer**: ES6 class managing NGL.js Stage, protein loading, highlighting, and state
- **VariantManager**: ES6 class handling variant list UI, sorting, and event management
- **Data Layer**: Variant objects exported from `variants.js` module
- **3D Visualization**: NGL.js-powered protein viewer that loads PDB structures from RCSB servers
- **Interactive UI**: Two-column layout with 3D viewer (left) and clickable variant list (right)

**Key Technical Patterns**:
- ES6 modules with import/export syntax
- Class-based architecture for encapsulation
- Uses NGL.js `Stage` and `Component` objects for 3D rendering
- Implements residue existence checking to handle incomplete PDB structures (2H8R only contains residues 170-280)
- Dynamic DOM manipulation for variant list generation with automatic sorting by pathogenicity
- Event-driven interaction model with click handlers for variant selection and view reset

## Development Commands

**Local Development**:
```bash
# Serve the HTML file locally for testing
python3 -m http.server 8000
# Then navigate to http://localhost:8000/hnf1b_variants.html
```

**No Build Process**: This is a static HTML file with no compilation or build steps required.

## Data Management

**Adding Variants**: Modify the `variants` array in `js/variants.js`:
```javascript
export const variants = [
    { name: 'p.VariantName', residue: 123, type: 'Pathogenic', color: 'red' }
    // Add new entries here
];
```

**Pathogenicity Classifications**: Use standard clinical significance terms:
- 'Pathogenic' (red)
- 'Likely Pathogenic' (orange) 
- 'Likely Benign' (#f5d547)
- 'Uncertain Significance' (grey)

## Technical Considerations

**PDB Structure Limitations**: The 2H8R structure is a fragment (residues 170-280). The application automatically disables variants outside this range and provides user feedback via tooltips.

**External Dependencies**: 
- NGL.js v2.0.0-dev.34 loaded from unpkg CDN
- PDB files fetched directly from RCSB servers

**Browser Compatibility**: Modern browsers required for ES6+ features and WebGL support for 3D rendering.