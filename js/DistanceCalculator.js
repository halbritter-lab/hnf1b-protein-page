// Distance calculation module for protein-DNA interactions
export class DistanceCalculator {
    constructor(proteinComponent) {
        this.proteinComponent = proteinComponent;
        this.dnaAtoms = [];
        this.distances = new Map();
        this.structure = null;
    }
    
    // Initialize and identify DNA atoms
    initialize() {
        if (!this.proteinComponent || !this.proteinComponent.structure) {
            console.error('Protein structure not loaded');
            return false;
        }
        
        this.structure = this.proteinComponent.structure;
        this.identifyDNAAtoms();
        return true;
    }
    
    // Identify and cache DNA atoms (phosphate backbone and bases)
    identifyDNAAtoms() {
        this.dnaAtoms = [];
        
        // Iterate through structure to find DNA residues
        this.structure.eachAtom((atomProxy) => {
            // Check if residue is DNA (DG, DC, DA, DT)
            const resname = atomProxy.resname;
            if (['DG', 'DC', 'DA', 'DT', 'G', 'C', 'A', 'T'].includes(resname)) {
                // Store important DNA atoms (phosphate backbone and base atoms)
                if (atomProxy.atomname === 'P' || 
                    atomProxy.atomname === 'C1\'' || 
                    atomProxy.atomname === 'N1' || 
                    atomProxy.atomname === 'N3') {
                    this.dnaAtoms.push({
                        index: atomProxy.index,
                        position: atomProxy.positionToVector3(),
                        atomname: atomProxy.atomname,
                        resname: resname,
                        resno: atomProxy.resno,
                        chainname: atomProxy.chainname
                    });
                }
            }
        });
        
        console.log(`Found ${this.dnaAtoms.length} DNA atoms for distance calculations`);
    }
    
    // Calculate distance from a specific residue to nearest DNA atom
    calculateResidueToHelixDistance(residueNumber, chainName = 'A') {
        if (this.dnaAtoms.length === 0) {
            console.warn('No DNA atoms found in structure');
            return null;
        }
        
        let minDistance = Infinity;
        let closestDNAAtom = null;
        let residueAtom = null;
        
        // Find the CA atom of the specified residue
        this.structure.eachAtom((atomProxy) => {
            if (atomProxy.resno === residueNumber && 
                atomProxy.chainname === chainName && 
                atomProxy.atomname === 'CA') {
                
                const residuePosition = atomProxy.positionToVector3();
                
                // Calculate distance to each DNA atom
                this.dnaAtoms.forEach(dnaAtom => {
                    const distance = residuePosition.distanceTo(dnaAtom.position);
                    if (distance < minDistance) {
                        minDistance = distance;
                        closestDNAAtom = dnaAtom;
                        residueAtom = {
                            index: atomProxy.index,
                            resno: atomProxy.resno,
                            chainname: atomProxy.chainname
                        };
                    }
                });
            }
        });
        
        if (minDistance === Infinity) {
            return null;
        }
        
        return {
            distance: minDistance,
            residueAtom: residueAtom,
            dnaAtom: closestDNAAtom
        };
    }
    
    // Calculate distances for all variants
    calculateAllDistances(variants) {
        this.distances.clear();
        
        variants.forEach(variant => {
            const result = this.calculateResidueToHelixDistance(variant.residue);
            if (result) {
                this.distances.set(variant.residue, result);
                // Store the distance directly on the variant object
                variant.distanceToDNA = result.distance;
                variant.closestDNAAtom = result.dnaAtom;
            } else {
                variant.distanceToDNA = null;
            }
        });
        
        return this.distances;
    }
    
    // Get distance category for coloring
    getDistanceCategory(distance) {
        if (distance === null) return 'unknown';
        if (distance < 5) return 'close';    // Direct contact
        if (distance < 10) return 'medium';  // Indirect interaction
        return 'far';                        // Distant
    }
    
    // Get formatted distance string
    formatDistance(distance) {
        if (distance === null) return 'N/A';
        return `${distance.toFixed(1)}Å`;
    }
}