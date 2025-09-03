# HNF1B Protein Variant Viewer

An interactive web-based visualization tool for exploring clinically relevant genetic variants on the 3D structure of HNF1B protein.

🔗 **Live Demo:** [https://halbritter-lab.github.io/hnf1b-protein-page/](https://halbritter-lab.github.io/hnf1b-protein-page/)

## Overview

This application provides an interactive 3D visualization of the HNF1B protein structure (PDB ID: 2H8R) with mapped genetic variants. Variants are color-coded by their clinical significance, allowing researchers and clinicians to explore the spatial distribution of pathogenic mutations.

## Features

- **Interactive 3D Visualization:** Rotate, zoom, and explore the protein structure using NGL.js
- **Variant Mapping:** Clinically relevant missense variants mapped onto the 3D structure
- **Pathogenicity Color-Coding:** Visual classification of variants by clinical significance
- **Distance Analysis:** Calculate distances between variants and DNA helix
- **Multiple Representations:** View protein in cartoon, surface, or ball-and-stick representations
- **Responsive Interface:** Two-column layout with 3D viewer and interactive variant list

## Technical Stack

- **Frontend:** Vanilla JavaScript (ES6 modules), HTML5, CSS3
- **3D Visualization:** NGL.js v2.0.0-dev.34
- **Data Analysis:** Python scripts for variant extraction and statistical analysis
- **Deployment:** GitHub Pages (static site hosting)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/halbritter-lab/hnf1b-protein-page.git
cd hnf1b-protein-page
```

2. Serve locally:
```bash
python3 -m http.server 8000
```

3. Open in browser:
```
http://localhost:8000
```

## Usage

### Adding New Variants

Edit the `js/variants.js` file:
```javascript
export const variants = [
    { name: 'p.Val173Ile', residue: 173, type: 'Pathogenic', color: 'red' },
    // Add new variants here
];
```

### Running Analysis Scripts

Extract variants from CSV data:
```bash
cd scripts
python extract-snv-variants.py
```

Analyze variant-DNA distances:
```bash
python analyze-variant-distances.py
```

## Data Sources

- **Protein Structure:** PDB ID 2H8R (HNF1B fragment, residues 170-280)
- **Variant Data:** Curated clinical genetics database
- **Clinical Significance:** ClinVar classifications

## Browser Requirements

- Modern browser with WebGL support
- ES6 module support
- JavaScript enabled

## Contributing

Contributions are welcome! Please submit issues and pull requests via GitHub.

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Citation

If you use this tool in your research, please cite:
```
HNF1B Protein Variant Viewer
https://github.com/halbritter-lab/hnf1b-protein-page
```

## Contact

For questions or support, please open an issue on GitHub.