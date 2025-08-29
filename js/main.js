// Application initialization and coordination
import { variants } from './variants.js';
import { ProteinViewer } from './ProteinViewer.js';
import { VariantManager } from './VariantManager.js';

document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Initialize protein viewer
        const proteinViewer = new ProteinViewer("viewport");
        
        // Initialize variant manager
        const variantManager = new VariantManager(variants, proteinViewer);
        
        // Load protein structure
        await proteinViewer.loadProtein("2H8R");
        
        // Get existing residues from the loaded structure
        const existingResidues = proteinViewer.getExistingResidues();
        
        // Populate variant list
        variantManager.populateVariantList(existingResidues);
        
        // Initialize event handlers
        variantManager.initializeEventHandlers();
        
    } catch (error) {
        console.error('Failed to initialize application:', error);
        // Could add user-friendly error message here
    }
});