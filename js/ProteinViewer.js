// NGL viewer management
export class ProteinViewer {
    constructor(containerId) {
        this.stage = new NGL.Stage(containerId);
        this.stage.setParameters({ backgroundColor: "white" });
        // Use passive: false to prevent the warning for resize events
        window.addEventListener("resize", () => this.stage.handleResize(), { passive: true });
        
        this.proteinComponent = null;
        this.currentHighlight = null;
        this.currentLabel = null;
        this.dnaRepresentation = null;
        this.dnaBaseRepresentation = null;
        this.distanceRepresentations = [];
        this.showingDNA = false;
        this.showingAllDistances = false;
    }
    
    async loadProtein(pdbId = "2H8R") {
        try {
            this.proteinComponent = await this.stage.loadFile(
                `https://files.rcsb.org/download/${pdbId}.pdb`, 
                { defaultRepresentation: false }
            );
            
            this.proteinComponent.addRepresentation("cartoon", { colorScheme: 'sstruc' });
            this.proteinComponent.autoView();
            
            return this.proteinComponent;
        } catch (error) {
            console.error('Failed to load protein:', error);
            throw error;
        }
    }
    
    getExistingResidues() {
        if (!this.proteinComponent) return new Set();
        
        const existingResidues = new Set();
        this.proteinComponent.structure.eachResidue(function(residueProxy) {
            if (residueProxy.chainname === 'A') {
                existingResidues.add(residueProxy.resno);
            }
        });
        
        return existingResidues;
    }
    
    focusOnVariant(variant) {
        if (!this.proteinComponent) return;

        // Clear previous highlights
        this.clearHighlights();

        const selectionString = `${variant.residue}:A`;
        
        // Add new representations
        this.currentHighlight = this.proteinComponent.addRepresentation("licorice", {
            sele: selectionString,
            color: "element", 
            scale: 2.0, 
            multipleBond: "symmetric"
        });

        this.currentLabel = this.proteinComponent.addRepresentation("label", {
            sele: `${selectionString} and .CA`,
            text: variant.name,
            color: variant.color,
            yOffset: 1.0,
            fontFamily: "sans-serif",
            fontWeight: "bold"
        });

        this.proteinComponent.autoView(selectionString, 1000);
    }
    
    resetView() {
        if (!this.proteinComponent) return;
        
        this.clearHighlights();
        this.proteinComponent.autoView(1000);
    }
    
    clearHighlights() {
        if (this.currentHighlight) {
            this.proteinComponent.removeRepresentation(this.currentHighlight);
            this.currentHighlight = null;
        }
        if (this.currentLabel) {
            this.proteinComponent.removeRepresentation(this.currentLabel);
            this.currentLabel = null;
        }
    }
    
    // DNA visualization methods
    toggleDNADisplay(show) {
        if (!this.proteinComponent) return;
        
        this.showingDNA = show;
        
        if (show) {
            // Add DNA cartoon representation
            this.dnaRepresentation = this.proteinComponent.addRepresentation("cartoon", {
                sele: "nucleic",
                color: "residueindex",
                opacity: 0.8
            });
            
            // Add DNA base representation
            this.dnaBaseRepresentation = this.proteinComponent.addRepresentation("base", {
                sele: "nucleic",
                color: "resname",
                opacity: 0.9
            });
        } else {
            // Remove DNA representations
            if (this.dnaRepresentation) {
                this.proteinComponent.removeRepresentation(this.dnaRepresentation);
                this.dnaRepresentation = null;
            }
            if (this.dnaBaseRepresentation) {
                this.proteinComponent.removeRepresentation(this.dnaBaseRepresentation);
                this.dnaBaseRepresentation = null;
            }
        }
    }
    
    // Show distance measurement between residue and DNA
    showDistanceMeasurement(variant, distanceInfo) {
        if (!this.proteinComponent || !distanceInfo) return;
        
        // Clear existing distance representations
        this.clearDistanceRepresentations();
        
        // Create atom pair for distance representation
        const atomPair = [
            `${variant.residue}:A.CA`,
            `${distanceInfo.dnaAtom.resno}:${distanceInfo.dnaAtom.chainname}.${distanceInfo.dnaAtom.atomname}`
        ];
        
        // Add distance representation
        const distanceRep = this.proteinComponent.addRepresentation("distance", {
            atomPair: [atomPair],
            color: "skyblue",
            labelSize: 1.0,
            labelColor: "black",
            labelVisible: true,
            labelUnit: "angstrom",
            labelPrecision: 1
        });
        
        this.distanceRepresentations.push(distanceRep);
    }
    
    // Clear all distance representations
    clearDistanceRepresentations() {
        this.distanceRepresentations.forEach(rep => {
            if (rep) {
                this.proteinComponent.removeRepresentation(rep);
            }
        });
        this.distanceRepresentations = [];
        this.showingAllDistances = false;
    }
    
    // Toggle all variant distances
    toggleAllDistances(variants, distanceMap) {
        if (!this.proteinComponent) return;
        
        if (this.showingAllDistances) {
            // Hide all distances
            this.clearDistanceRepresentations();
            this.showingAllDistances = false;
        } else {
            // Show all distances
            this.clearDistanceRepresentations();
            
            variants.forEach(variant => {
                const distanceInfo = distanceMap.get(variant.residue);
                if (distanceInfo) {
                    const atomPair = [
                        `${variant.residue}:A.CA`,
                        `${distanceInfo.dnaAtom.resno}:${distanceInfo.dnaAtom.chainname}.${distanceInfo.dnaAtom.atomname}`
                    ];
                    
                    const distanceRep = this.proteinComponent.addRepresentation("distance", {
                        atomPair: [atomPair],
                        color: this.getDistanceColor(distanceInfo.distance),
                        labelSize: 0.8,
                        labelColor: "black",
                        labelVisible: true,
                        labelUnit: "angstrom",
                        labelPrecision: 1
                    });
                    
                    this.distanceRepresentations.push(distanceRep);
                }
            });
            
            this.showingAllDistances = true;
        }
        
        return this.showingAllDistances;
    }
    
    // Get color based on distance
    getDistanceColor(distance) {
        if (distance < 5) return "#d32f2f";   // Red for close
        if (distance < 10) return "#ff9800";  // Orange for medium
        return "#4caf50";                      // Green for far
    }
}