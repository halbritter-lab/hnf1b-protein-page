// Manages protein representation types and configurations
export class RepresentationManager {
    constructor() {
        // Define available representations with their configurations
        // Simplified set of most useful representations
        this.representations = {
            cartoon: {
                name: 'Cartoon',
                config: { 
                    colorScheme: 'sstruc',
                    quality: 'high'
                },
                description: 'Secondary structure visualization with helices and sheets'
            },
            surface: {
                name: 'Surface',
                config: { 
                    colorScheme: 'hydrophobicity',
                    surfaceType: 'sas'  // Solvent accessible surface
                },
                description: 'Molecular surface showing binding pockets and hydrophobic regions'
            },
            'ball+stick': {
                name: 'Ball & Stick',
                config: { 
                    colorScheme: 'element',
                    aspectRatio: 2.0,  // Ball to stick ratio
                    radiusScale: 0.5
                },
                description: 'Classic molecular model with atoms as spheres and bonds as sticks'
            },
            licorice: {
                name: 'Sticks',
                config: { 
                    colorScheme: 'element',
                    multipleBond: 'symmetric'
                },
                description: 'Stick representation showing all atoms and bonds'
            },
            ribbon: {
                name: 'Ribbon',
                config: { 
                    colorScheme: 'sstruc',
                    thickness: 0.4
                },
                description: 'Simplified backbone ribbon following the protein chain'
            },
            backbone: {
                name: 'Backbone',
                config: { 
                    colorScheme: 'residueindex',
                    scale: 0.3
                },
                description: 'Minimal backbone trace showing the protein fold'
            }
        };
        
        // Available color schemes for all representations
        this.colorSchemes = {
            sstruc: 'Secondary Structure',
            element: 'Element',
            residueindex: 'Rainbow by Position',
            hydrophobicity: 'Hydrophobicity',
            bfactor: 'B-factor (Temperature)',
            chainindex: 'Chain',
            uniform: 'Single Color'
        };
        
        // Track current settings
        this.currentRepresentation = 'cartoon';
        this.currentColorScheme = 'sstruc';
        this.currentOpacity = 1.0;  // Default to fully opaque
        this.showSidechains = false;
    }
    
    // Get configuration for a specific representation
    getRepresentationConfig(type, customOptions = {}) {
        const baseConfig = this.representations[type]?.config || {};
        
        // Merge with custom options
        const config = {
            ...baseConfig,
            ...customOptions,
            sele: 'protein'  // Only show protein, not DNA
        };
        
        // Apply current settings
        if (this.currentColorScheme && this.currentColorScheme !== 'default') {
            config.colorScheme = this.currentColorScheme;
        }
        
        // Always apply opacity for representations that support it
        if (this.supportsOpacity(type)) {
            config.opacity = this.currentOpacity;
        }
        
        return config;
    }
    
    // Get list of available representations
    getAvailableRepresentations() {
        return Object.entries(this.representations).map(([key, value]) => ({
            value: key,
            name: value.name,
            description: value.description
        }));
    }
    
    // Get list of available color schemes
    getAvailableColorSchemes() {
        return Object.entries(this.colorSchemes).map(([key, value]) => ({
            value: key,
            name: value
        }));
    }
    
    // Update current settings
    updateSettings(settings) {
        if (settings.representation !== undefined) {
            this.currentRepresentation = settings.representation;
        }
        if (settings.colorScheme !== undefined) {
            this.currentColorScheme = settings.colorScheme;
        }
        if (settings.opacity !== undefined) {
            this.currentOpacity = settings.opacity;
        }
        if (settings.showSidechains !== undefined) {
            this.showSidechains = settings.showSidechains;
        }
    }
    
    // Get sidechain configuration
    getSidechainConfig() {
        return {
            sele: 'protein and sidechainAttached',
            colorScheme: 'element',
            opacity: 0.6
        };
    }
    
    // Check if representation supports transparency
    supportsOpacity(type) {
        return ['surface', 'cartoon', 'ribbon'].includes(type);
    }
    
    // Check if representation works well with sidechains
    supportsSidechains(type) {
        return ['cartoon', 'ribbon', 'backbone'].includes(type);
    }
}