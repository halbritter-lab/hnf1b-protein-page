// Variant data handling and UI management
export class VariantManager {
    constructor(variants, proteinViewer) {
        this.variants = variants;
        this.proteinViewer = proteinViewer;
    }
    
    populateVariantList(existingResidues) {
        const listElement = document.getElementById('variant-list');
        listElement.innerHTML = ''; 

        // Sort variants by pathogenic significance
        const rank = { 
            'Pathogenic': 1, 
            'Likely Pathogenic': 2, 
            'Likely Benign': 3, 
            'Uncertain Significance': 4 
        };
        const sortedVariants = [...this.variants].sort((a, b) => rank[a.type] - rank[b.type]);

        sortedVariants.forEach(variant => {
            const item = document.createElement('li');
            item.dataset.variant = JSON.stringify(variant);
            
            const residueExists = existingResidues.has(variant.residue);

            if (!residueExists) {
                item.classList.add('disabled');
                item.title = `Residue ${variant.residue} is not resolved in the PDB structure and cannot be shown.`;
            }

            item.innerHTML = `
                <div class="color-dot" style="background-color: ${residueExists ? variant.color : '#ccc'};"></div>
                <div>
                    <strong>${variant.name}</strong><br>
                    <small>Significance: ${variant.type}</small>
                </div>
            `;
            listElement.appendChild(item);
        });
    }
    
    initializeEventHandlers() {
        // Variant list click handler
        document.getElementById('variant-list').addEventListener('click', (event) => {
            const clickedItem = event.target.closest('li');
            if (clickedItem && !clickedItem.classList.contains('disabled')) {
                const variantData = JSON.parse(clickedItem.dataset.variant);
                this.proteinViewer.focusOnVariant(variantData);
            }
        });
        
        // Reset view button handler
        document.getElementById('reset-view-btn').addEventListener('click', () => {
            this.proteinViewer.resetView();
        });
    }
}