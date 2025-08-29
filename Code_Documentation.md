# Code Documentation: HNF1B Variant Viewer

This document provides a detailed, beginner-friendly explanation of the current `hnf1b_interactive.html` file.

Our `hnf1b_interactive.html` file is a self-contained webpage. It can be understood in three main parts: the HTML (the skeleton), the CSS (the paint and clothes), and the JavaScript (the brain and nervous system).

### 1. The HTML Structure (`<body>` section)

This is the content and structure of the page.

```html
<!-- This is the main title you see at the top of the page. -->
<h1>HNF1B Interactive Variant Viewer (PDB: 2H8R)</h1>

<!-- This is the main container that holds our two columns. -->
<div class="main-container">

    <!-- This is the LEFT column, where the 3D protein viewer will live. -->
    <!-- The id="viewport" is a special name so JavaScript knows where to build the viewer. -->
    <div id="viewport" class="viewer-container"></div>

    <!-- This is the RIGHT column, which holds our controls and variant list. -->
    <div class="variant-container">
        <h2>Variants</h2>
        
        <!-- This is our "Reset View" button. -->
        <button id="reset-view-btn">Reset View</button>
        
        <p>Click a variant to highlight it on the structure.</p>
        
        <!-- This is an empty, unordered list. JavaScript will automatically fill this -->
        <!-- with our clickable list of variants. -->
        <ul id="variant-list"></ul>
    </div>
</div>

<!-- This line is crucial! It downloads and loads the NGL.js library, -->
<!-- which provides all the 3D graphics and protein viewing power. -->
<script src="https://unpkg.com/ngl@2.0.0-dev.34/dist/ngl.js" type="text/javascript"></script>

<!-- This is where our custom JavaScript code lives, which controls everything. -->
<script>
    // ... all the JavaScript logic ...
</script> 
```
### The CSS Styling (`<style>` section)
This code controls how the HTML elements look (colors, sizes, layout).

```css
/* Sets a nice font for the whole page. */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* This is the magic for the two-column layout. */
.main-container {
    display: flex; /* Arranges its children (the two columns) side-by-side. */
}

/* Styles the LEFT column (the viewer). */
.viewer-container {
    flex: 3; /* Tells it to take up 3 "parts" of the available width. */
    height: 80vh; /* Sets its height to 80% of the browser window's height. */
}

/* Styles the RIGHT column (the variant list). */
.variant-container {
    flex: 2; /* Tells it to take up 2 "parts" of the width. (3:2 ratio) */
    height: 80vh; /* Matches the viewer's height. */
    overflow-y: auto; /* If the list is too long, a scrollbar will appear. */
}

/* Styles our "Reset" button to make it look nice. */
#reset-view-btn {
    display: block;
    width: 100%;
    /* ... other visual styles like color, padding, etc. ... */
}

/* This special style applies ONLY to list items that we've marked as "disabled". */
#variant-list li.disabled {
    cursor: not-allowed; /* Shows a "do not enter" cursor. */
    color: #999; /* Fades the text to grey. */
}
```
### The JavaScript Logic (`<script>` section)
This is the "brain" of the application that makes everything interactive. It's executed by the browser after the page has loaded.

```javascript
// This is the "master switch". It tells the browser to wait until the entire HTML
// document is loaded and ready before trying to run any of our code.
document.addEventListener('DOMContentLoaded', function() {

    // --- The Data ---
    // This is our central database. It's an array of JavaScript objects.
    // Each object holds all the information for one variant. Adding or changing
    // variants here is all you need to do to update the list.
    const variants = [
        { name: 'p.Val173Ile', residue: 173, type: 'Uncertain Significance', color: 'grey' },
        // ... more variants
    ];

    // --- Initialization ---
    // This line creates the NGL viewer "stage" inside our <div id="viewport">.
    var stage = new NGL.Stage("viewport");
    
    // These variables act as the script's "memory". They will hold references to
    // the protein model and the currently active highlight, so we can control them later.
    let proteinComponent = null;
    let currentHighlight = null;
    let currentLabel = null;

    // --- The Core Functions (The "Skills" of our App) ---

    // This function is called when you click a variant.
    function focusOnVariant(variant) {
        // 1. If a highlight from a previous click exists, remove it.
        if (currentHighlight) { proteinComponent.removeRepresentation(currentHighlight); }
        if (currentLabel) { proteinComponent.removeRepresentation(currentLabel); }

        // 2. Create the new highlight ("licorice" view) and the colored label.
        currentHighlight = proteinComponent.addRepresentation("licorice", { /* ...options... */ });
        currentLabel = proteinComponent.addRepresentation("label", { text: variant.name, color: variant.color, /* ...options... */ });

        // 3. Zoom the camera to focus on the new highlight.
        proteinComponent.autoView(`${variant.residue}:A`, 1000);
    }

    // This function is called when you click the "Reset View" button.
    function resetView() {
        // 1. Remove any active highlight.
        if (currentHighlight) { proteinComponent.removeRepresentation(currentHighlight); }
        if (currentLabel) { proteinComponent.removeRepresentation(currentLabel); }
        // 2. Clear our "memory" variables.
        currentHighlight = null;
        currentLabel = null;
        // 3. Zoom the camera back out to the whole protein.
        proteinComponent.autoView(1000);
    }

    // This function builds the clickable list on the right side of the page.
    function populateVariantList(existingResidues) {
        // 1. Sort the `variants` array by pathogenicity.
        // 2. Loop through each variant in our data array.
        variants.forEach(variant => {
            // 3. For each variant, check if its residue number actually exists in the 3D model.
            const residueExists = existingResidues.has(variant.residue);

            // 4. Create an HTML list item (<li>).
            // 5. If the residue doesn't exist, give the item the "disabled" CSS style.
            // 6. Add the final HTML item to the list on the webpage.
        });
    }

    // --- The Main Execution Flow ---
    // This is what kicks everything off.
    
    // 1. Start downloading the PDB file from the internet.
    stage.loadFile("https://files.rcsb.org/download/2H8R.pdb", { /* ...options... */ })
        // 2. The `.then()` command means: "When the file has successfully loaded, do the following..."
        .then(function (component) {
            
            // a. Save a reference to the loaded protein in our "memory".
            proteinComponent = component;
            // b. Add the default "cartoon" view of the protein.
            proteinComponent.addRepresentation("cartoon", { /* ...options... */ });
            
            // c. Create a list of all residues that physically exist in the model.
            const existingResidues = new Set();
            component.structure.eachResidue(residueProxy => {
                existingResidues.add(residueProxy.resno);
            });

            // d. Now, build the interactive variant menu using this list of existing residues.
            populateVariantList(existingResidues);

            // e. Finally, activate the click listeners for the variant list and the reset button.
            document.getElementById('variant-list').addEventListener('click', /* ... */);
            document.getElementById('reset-view-btn').addEventListener('click', resetView);
            
            // f. Set the initial camera view.
            proteinComponent.autoView();
        });
});
```