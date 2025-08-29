# hnf1b-protein-page

# Interactive HNF1B Variant Viewer

This project is a self-contained HTML webpage for visualizing clinically relevant genetic variants on a 3D structure of the HNF1B protein. It allows users to see the location of specific variants, color-coded by their pathogenic significance, on an experimental structure from the Protein Data Bank (PDB).

## Project Development Journey

This tool was developed through an iterative process of brainstorming, implementation, and debugging.

### 1. Initial Goal & Technology Choice
The initial goal was to create a simple web page to display missense variants on the HNF1B protein structure (PDB ID: 2H8R). The JavaScript library `Michelanglo.js`, a user-friendly wrapper for the powerful `NGL.js` viewer, was chosen as the starting point.

### 2. Early Challenges & Technical Pivot
Initial attempts using the Michelanglo library ran into several issues:
- **Network Errors:** The default method for fetching protein structures failed due to DNS resolution issues.
- **Library-Specific Bugs:** The Michelanglo wrapper produced cryptic errors when trying to load the structure from a direct URL.
- **Dependency Conflicts:** Attempts to bypass the wrapper led to conflicts with its jQuery dependency.

These challenges led to a crucial decision: to abandon the Michelanglo wrapper and use the core **NGL.js library** directly. This provided more control, stability, and removed unnecessary dependencies.

### 3. Building an Interactive Tool
With a stable viewer in place, the project evolved from a static visualization into an interactive tool:
- **Two-Column Layout:** The interface was redesigned to have the 3D viewer on the left and a clickable list of variants on the right.
- **Data-Driven Approach:** A JavaScript array of variant "objects" was created to act as a central, easily updatable database for the application.
- **Dynamic List Generation:** The clickable list is now generated automatically from this data array.
- **Interactivity:** Clicking a variant in the list now highlights it on the protein structure and zooms the camera to focus on it.

### 4. Key Scientific and Technical Refinements
The final stage of development focused on scientific accuracy and user experience:
- **Handling Incomplete Structures:** A major realization was that the PDB file (`2H8R`) is only a fragment of the full protein (residues 170-280). The script was upgraded to programmatically check which variants exist within the loaded model. Variants that are out of range or in missing/unresolved loops (like p.Asn228Lys) are now automatically disabled in the list, with an informative tooltip.
- **Improved Visualization:** The default highlight was replaced with a more chemically informative "licorice" representation. Crucially, the label was changed to show the full variant name (e.g., "p.Val173Ile") and was color-coded according to its pathogenic significance.
- **Robust State Management:** A persistent bug where old highlights would remain on the screen was fixed by implementing a stateful system. The script now keeps a direct reference to the currently active highlight, ensuring it can be reliably removed before a new one is shown.
- **User-Friendly Features:** A "Reset View" button was added to clear all highlights and return to the default view of the entire protein. The variant list is also automatically sorted by pathogenic significance.

This iterative process of identifying problems and implementing robust solutions resulted in a scientifically accurate, user-friendly, and powerful bioinformatics visualization tool.