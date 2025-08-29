// NGL viewer management
export class ProteinViewer {
    constructor(containerId) {
        this.stage = new NGL.Stage(containerId);
        this.stage.setParameters({ backgroundColor: "white" });
        window.addEventListener("resize", () => this.stage.handleResize(), false);
        
        this.proteinComponent = null;
        this.currentHighlight = null;
        this.currentLabel = null;
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
}