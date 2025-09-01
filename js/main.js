// Application initialization and coordination
import { variants } from './variants.js';
import { ProteinViewer } from './ProteinViewer.js';
import { VariantManager } from './VariantManager.js';
import { DistanceCalculator } from './DistanceCalculator.js';

document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Initialize protein viewer
        const proteinViewer = new ProteinViewer("viewport");
        
        // Initialize variant manager
        const variantManager = new VariantManager(variants, proteinViewer);
        
        // Load protein structure
        await proteinViewer.loadProtein("2H8R");
        
        // Initialize distance calculator
        const distanceCalculator = new DistanceCalculator(proteinViewer.proteinComponent);
        if (distanceCalculator.initialize()) {
            // Calculate distances for all variants
            const distanceMap = distanceCalculator.calculateAllDistances(variants);
            
            // Update variant manager with distance information
            variantManager.setDistanceCalculator(distanceCalculator);
            variantManager.setDistanceMap(distanceMap);
            
            console.log('Distance calculations completed:', distanceMap.size, 'variants analyzed');
        } else {
            console.warn('Distance calculator initialization failed - DNA distance features disabled');
        }
        
        // Get existing residues from the loaded structure
        const existingResidues = proteinViewer.getExistingResidues();
        
        // Populate variant list (will now include distance information)
        variantManager.populateVariantList(existingResidues);
        
        // Initialize event handlers
        variantManager.initializeEventHandlers();
        
    } catch (error) {
        console.error('Failed to initialize application:', error);
        // Could add user-friendly error message here
    }
});