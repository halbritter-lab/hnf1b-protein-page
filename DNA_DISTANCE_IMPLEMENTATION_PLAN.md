# Implementation Plan: DNA Distance Visualization for HNF1B Protein Viewer

## Overview
Expand the existing HNF1B protein visualization tool to include distance measurements between protein residues and the DNA helix. The PDB structure 2H8R contains both the HNF1B DNA-binding domain and bound DNA, making this enhancement feasible using NGL.js's built-in distance measurement capabilities.

## Implementation Approach

### 1. Core Distance Calculation Module
**New File: `js/DistanceCalculator.js`**
- Class to handle distance calculations between protein residues and DNA atoms
- Methods to identify DNA atoms (phosphate backbone)
- Calculate minimum distance from each variant residue to DNA helix
- Cache results for performance

### 2. Visual Distance Display
**Extend `js/ProteinViewer.js`**
- Add distance visualization using NGL's "distance" representation
- Toggle DNA display (cartoon/base representations)
- Show distance measurements as dashed lines between atoms
- Color-code distances by proximity ranges

### 3. UI Enhancements
**Update `js/VariantManager.js`**
- Display distance values next to each variant
- Add sorting by distance to DNA
- Color-code variants based on proximity (< 5Å direct contact, 5-10Å indirect, > 10Å distant)

### 4. New UI Controls
**Add to `index.html` and create `css/distances.css`**
- Toggle button for DNA visibility
- Distance filter dropdown
- Show all distances button
- Visual indicators for distance ranges

## Technical Implementation

### NGL.js Features to Utilize
- **Distance representation**: `addRepresentation("distance", {atomPair: [...]})`
- **DNA selection**: `sele: "nucleic"` for DNA residues
- **Atom coordinates**: Access via `structure.eachAtom()` for calculations

### Key Code Structures

```javascript
// Distance visualization example
showDistanceMeasurement(residue, dnaAtom) {
    this.proteinComponent.addRepresentation("distance", {
        atomPair: [[`${residue}:A.CA`, dnaAtom]]
    });
}

// DNA display toggle
toggleDNADisplay(show) {
    if (show) {
        this.proteinComponent.addRepresentation("cartoon", {
            sele: "nucleic",
            color: "resname"
        });
    }
}
```

### Data Structure Update
Extend variant objects with distance property:
```javascript
{ 
    name: 'p.R177W', 
    residue: 177, 
    type: 'Pathogenic', 
    color: 'red',
    distanceToDNA: null  // Populated dynamically
}
```

## Expected Outcomes

### Functional Benefits
- Quantitative assessment of variant proximity to DNA
- Visual confirmation of DNA-binding relevance
- Better understanding of pathogenicity mechanisms

### Scientific Value
- Identify variants directly affecting DNA binding (< 5Å)
- Distinguish between DNA-contact and structural variants
- Support hypothesis generation about variant effects