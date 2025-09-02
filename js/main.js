// Application initialization and coordination
import { variants } from './variants.js';
import { ProteinViewer } from './protein-viewer.js';
import { VariantManager } from './variant-manager.js';
import { DistanceCalculator } from './distance-calculator.js';
import { RepresentationManager } from './representation-manager.js';

document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Initialize protein viewer
        const proteinViewer = new ProteinViewer("viewport");
        
        // Initialize representation manager and attach to viewer
        const representationManager = new RepresentationManager();
        proteinViewer.setRepresentationManager(representationManager);
        
        // Initialize variant manager
        const variantManager = new VariantManager(variants, proteinViewer);
        
        // Load protein structure
        await proteinViewer.loadProtein("2H8R");
        
        // Show DNA by default
        proteinViewer.toggleDNADisplay(true);
        
        // Initialize distance calculator
        const distanceCalculator = new DistanceCalculator(proteinViewer.proteinComponent);
        if (distanceCalculator.initialize()) {
            // Calculate distances for all variants (default to using closest atom)
            const useClosestAtom = document.getElementById('use-sidechain-distance').checked;
            const distanceMap = distanceCalculator.calculateAllDistances(variants, useClosestAtom);
            
            // Update variant manager with distance information
            variantManager.setDistanceCalculator(distanceCalculator);
            variantManager.setDistanceMap(distanceMap);
            
            console.log('Distance calculations completed:', distanceMap.size, 'variants analyzed');
            
            // Expose distance calculator for debugging
            window.distanceCalculator = distanceCalculator;
            console.log('Distance calculator available for testing. Try: distanceCalculator.testDistanceCalculation(295)');
            
            // Add event listener for distance mode toggle
            document.getElementById('use-sidechain-distance').addEventListener('change', (event) => {
                const useClosest = event.target.checked;
                console.log(`Recalculating distances using ${useClosest ? 'closest atom' : 'CA only'} method...`);
                
                // Recalculate all distances with new method
                const newDistanceMap = distanceCalculator.calculateAllDistances(variants, useClosest);
                variantManager.setDistanceMap(newDistanceMap);
                
                // Refresh the variant list to show updated distances
                const existingResidues = proteinViewer.getExistingResidues();
                variantManager.populateVariantList(existingResidues);
            });
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