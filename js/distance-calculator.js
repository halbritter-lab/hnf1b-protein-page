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
        
        // Check structure completeness
        this.checkStructureCompleteness();
        
        return true;
    }
    
    // Check if structure has sidechains or is CA-only
    checkStructureCompleteness() {
        let totalAtoms = 0;
        let proteinAtoms = 0;
        let caAtoms = 0;
        let sidechainAtoms = 0;
        
        this.structure.eachAtom((atomProxy) => {
            totalAtoms++;
            
            // Check if it's a protein atom (not DNA/water/ligand)
            const resname = atomProxy.resname;
            const isProtein = !['DG', 'DC', 'DA', 'DT', 'G', 'C', 'A', 'T', 'HOH', 'WAT'].includes(resname);
            
            if (isProtein) {
                proteinAtoms++;
                if (atomProxy.atomname === 'CA') {
                    caAtoms++;
                } else if (!['N', 'C', 'O', 'CA'].includes(atomProxy.atomname) && 
                          !atomProxy.atomname.startsWith('H')) {
                    sidechainAtoms++;
                }
            }
        });
        
        console.log('Structure analysis:', {
            totalAtoms,
            proteinAtoms,
            caAtoms,
            sidechainAtoms,
            hasSidechains: sidechainAtoms > 0,
            atomsPerResidue: caAtoms > 0 ? (proteinAtoms / caAtoms).toFixed(1) : 'N/A'
        });
        
        if (sidechainAtoms === 0 && caAtoms > 0) {
            console.warn('⚠️ This appears to be a CA-only structure. Sidechain distance calculations will not provide different results.');
        }
    }
    
    // Identify and cache DNA atoms (all non-hydrogen atoms for accurate distance)
    identifyDNAAtoms() {
        this.dnaAtoms = [];
        
        // Iterate through structure to find DNA residues
        this.structure.eachAtom((atomProxy) => {
            // Check if residue is DNA (DG, DC, DA, DT)
            const resname = atomProxy.resname;
            if (['DG', 'DC', 'DA', 'DT', 'G', 'C', 'A', 'T'].includes(resname)) {
                // Store all non-hydrogen DNA atoms for accurate distance calculations
                if (!atomProxy.atomname.startsWith('H')) {
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
    // Uses closest atom approach - checks all atoms in the residue including sidechains
    calculateResidueToHelixDistance(residueNumber, chainName = 'A', useClosestAtom = true) {
        if (this.dnaAtoms.length === 0) {
            console.warn('No DNA atoms found in structure');
            return null;
        }
        
        let minDistance = Infinity;
        let closestDNAAtom = null;
        let closestResidueAtom = null;
        let residueAtoms = [];
        
        // Collect all atoms from the specified residue
        this.structure.eachAtom((atomProxy) => {
            if (atomProxy.resno === residueNumber && 
                atomProxy.chainname === chainName &&
                !atomProxy.atomname.startsWith('H')) { // Exclude hydrogens for performance
                
                residueAtoms.push({
                    index: atomProxy.index,
                    position: atomProxy.positionToVector3(),
                    atomname: atomProxy.atomname,
                    resno: atomProxy.resno,
                    chainname: atomProxy.chainname,
                    element: atomProxy.element
                });
            }
        });
        
        if (residueAtoms.length === 0) {
            return null;
        }
        
        // Debug: Log atom collection for specific residues
        if (residueNumber === 177 || residueNumber === 295) {
            console.log(`Residue ${residueNumber} atoms found:`, 
                residueAtoms.map(a => a.atomname).join(', '), 
                `(${residueAtoms.length} atoms)`);
        }
        
        // Find the closest distance between any residue atom and any DNA atom
        if (useClosestAtom) {
            // Check all atoms in the residue to find the closest one to DNA
            residueAtoms.forEach(residueAtom => {
                this.dnaAtoms.forEach(dnaAtom => {
                    const distance = residueAtom.position.distanceTo(dnaAtom.position);
                    if (distance < minDistance) {
                        minDistance = distance;
                        closestDNAAtom = dnaAtom;
                        closestResidueAtom = residueAtom;
                    }
                });
            });
        } else {
            // Use only CA atom for distance (original behavior)
            const caAtom = residueAtoms.find(atom => atom.atomname === 'CA');
            if (caAtom) {
                this.dnaAtoms.forEach(dnaAtom => {
                    const distance = caAtom.position.distanceTo(dnaAtom.position);
                    if (distance < minDistance) {
                        minDistance = distance;
                        closestDNAAtom = dnaAtom;
                        closestResidueAtom = caAtom;
                    }
                });
            }
        }
        
        if (minDistance === Infinity) {
            return null;
        }
        
        // Debug: Compare CA distance vs closest atom distance for specific residues
        if ((residueNumber === 177 || residueNumber === 295) && useClosestAtom) {
            const caAtom = residueAtoms.find(atom => atom.atomname === 'CA');
            if (caAtom) {
                let caMinDistance = Infinity;
                this.dnaAtoms.forEach(dnaAtom => {
                    const distance = caAtom.position.distanceTo(dnaAtom.position);
                    if (distance < caMinDistance) {
                        caMinDistance = distance;
                    }
                });
                console.log(`Residue ${residueNumber} distances:`,
                    `CA=${caMinDistance.toFixed(2)}Å,`,
                    `Closest=${minDistance.toFixed(2)}Å (${closestResidueAtom.atomname}),`,
                    `Difference=${(caMinDistance - minDistance).toFixed(2)}Å`);
            }
        }
        
        return {
            distance: minDistance,
            residueAtom: closestResidueAtom,
            dnaAtom: closestDNAAtom,
            measurementType: useClosestAtom ? 'closest-atom' : 'CA-only'
        };
    }
    
    // Calculate distances for all variants
    calculateAllDistances(variants, useClosestAtom = true) {
        this.distances.clear();
        
        variants.forEach(variant => {
            const result = this.calculateResidueToHelixDistance(variant.residue, 'A', useClosestAtom);
            if (result) {
                this.distances.set(variant.residue, result);
                // Store the distance and atom details directly on the variant object
                variant.distanceToDNA = result.distance;
                variant.closestDNAAtom = result.dnaAtom;
                variant.closestResidueAtom = result.residueAtom;
                variant.measurementType = result.measurementType;
            } else {
                variant.distanceToDNA = null;
                variant.closestResidueAtom = null;
            }
        });
        
        console.log(`Calculated distances for ${variants.length} variants using ${useClosestAtom ? 'closest atom' : 'CA only'} method`);
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
    
    // Test function to verify distance calculations
    testDistanceCalculation(residueNumber = 295) {
        console.log(`\n=== Testing distance calculation for residue ${residueNumber} ===`);
        
        // Test with CA only
        const caResult = this.calculateResidueToHelixDistance(residueNumber, 'A', false);
        console.log('CA-only result:', caResult ? {
            distance: caResult.distance.toFixed(2) + 'Å',
            atom: caResult.residueAtom.atomname,
            dnaAtom: `${caResult.dnaAtom.atomname} of ${caResult.dnaAtom.resname}${caResult.dnaAtom.resno}`
        } : 'null');
        
        // Test with closest atom
        const closestResult = this.calculateResidueToHelixDistance(residueNumber, 'A', true);
        console.log('Closest-atom result:', closestResult ? {
            distance: closestResult.distance.toFixed(2) + 'Å',
            atom: closestResult.residueAtom.atomname,
            dnaAtom: `${closestResult.dnaAtom.atomname} of ${closestResult.dnaAtom.resname}${closestResult.dnaAtom.resno}`
        } : 'null');
        
        if (caResult && closestResult) {
            const difference = caResult.distance - closestResult.distance;
            console.log(`Difference: ${difference.toFixed(2)}Å (CA is ${difference > 0 ? 'farther' : 'closer'})`);
        }
        
        console.log('=== Test complete ===\n');
    }
}