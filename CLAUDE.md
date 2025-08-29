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
- **ProteinViewer**: ES6 class managing NGL.js Stage, protein loading, highlighting, and state management. Handles PDB loading from RCSB servers, residue existence checking, and 3D representation control.
- **VariantManager**: ES6 class handling variant list UI, sorting by pathogenicity, and DOM event management. Manages variant-to-viewer communication and dynamic list population.
- **Data Layer**: Variant objects exported from `variants.js` module with standardized schema (name, residue, type, color)
- **Application Coordinator**: `main.js` orchestrates initialization sequence: viewer setup → protein loading → residue validation → UI population → event binding

**Key Technical Patterns**:
- ES6 modules with import/export syntax for clean dependency management
- Class-based architecture with clear separation of concerns
- Uses NGL.js `Stage` and `Component` objects for 3D rendering with stateful highlight management
- Implements residue existence checking to handle incomplete PDB structures (2H8R fragment contains residues 170-280)
- Dynamic DOM manipulation with automatic pathogenicity-based sorting
- Event-driven interaction model with delegation for scalable variant list handling
- Async/await pattern for protein loading with proper error handling

## Development Commands

**Local Development**:
```bash
# Serve the HTML file locally for testing
python3 -m http.server 8000
# Then navigate to http://localhost:8000/index.html
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