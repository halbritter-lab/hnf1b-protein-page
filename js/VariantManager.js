// Variant data handling and UI management
export class VariantManager {
    constructor(variants, proteinViewer, distanceCalculator = null) {
        this.variants = variants;
        this.proteinViewer = proteinViewer;
        this.distanceCalculator = distanceCalculator;
        this.sortMode = 'pathogenicity'; // 'pathogenicity' or 'distance'
        this.distanceMap = null;
    }
    
    setDistanceCalculator(distanceCalculator) {
        this.distanceCalculator = distanceCalculator;
    }
    
    setDistanceMap(distanceMap) {
        this.distanceMap = distanceMap;
    }
    
    setSortMode(mode) {
        this.sortMode = mode;
        const existingResidues = this.proteinViewer.getExistingResidues();
        this.populateVariantList(existingResidues);
    }
    
    populateVariantList(existingResidues) {
        const listElement = document.getElementById('variant-list');
        listElement.innerHTML = ''; 

        // Sort variants based on current sort mode
        let sortedVariants;
        if (this.sortMode === 'distance' && this.distanceMap) {
            // Sort by distance to DNA
            sortedVariants = [...this.variants].sort((a, b) => {
                const distA = a.distanceToDNA || Infinity;
                const distB = b.distanceToDNA || Infinity;
                return distA - distB;
            });
        } else {
            // Sort by pathogenic significance (default)
            const rank = { 
                'Pathogenic': 1, 
                'Likely Pathogenic': 2, 
                'Likely Benign': 3, 
                'Uncertain Significance': 4 
            };
            sortedVariants = [...this.variants].sort((a, b) => rank[a.type] - rank[b.type]);
        }

        sortedVariants.forEach(variant => {
            const item = document.createElement('li');
            item.dataset.variant = JSON.stringify(variant);
            
            const residueExists = existingResidues.has(variant.residue);

            if (!residueExists) {
                item.classList.add('disabled');
                item.title = `Residue ${variant.residue} is not resolved in the PDB structure and cannot be shown.`;
            }
            
            // Format distance display
            let distanceDisplay = '';
            if (this.distanceMap && residueExists) {
                const distanceInfo = this.distanceMap.get(variant.residue);
                if (distanceInfo) {
                    const distance = distanceInfo.distance;
                    const category = this.getDistanceCategory(distance);
                    distanceDisplay = `<small class="distance-info distance-${category}">Distance to DNA: ${distance.toFixed(1)}Å</small>`;
                }
            }

            item.innerHTML = `
                <div class="color-dot" style="background-color: ${residueExists ? variant.color : '#ccc'};"></div>
                <div class="variant-info">
                    <strong>${variant.name}</strong><br>
                    <small>Significance: ${variant.type}</small>
                    ${distanceDisplay}
                </div>
            `;
            listElement.appendChild(item);
        });
    }
    
    getDistanceCategory(distance) {
        if (distance < 5) return 'close';
        if (distance < 10) return 'medium';
        return 'far';
    }
    
    initializeEventHandlers() {
        // Variant list click handler
        document.getElementById('variant-list').addEventListener('click', (event) => {
            const clickedItem = event.target.closest('li');
            if (clickedItem && !clickedItem.classList.contains('disabled')) {
                const variantData = JSON.parse(clickedItem.dataset.variant);
                this.proteinViewer.focusOnVariant(variantData);
                
                // Show distance measurement if available
                if (this.distanceMap) {
                    const distanceInfo = this.distanceMap.get(variantData.residue);
                    if (distanceInfo) {
                        this.proteinViewer.showDistanceMeasurement(variantData, distanceInfo);
                    }
                }
            }
        });
        
        // Reset view button handler
        document.getElementById('reset-view-btn').addEventListener('click', () => {
            this.proteinViewer.resetView();
            this.proteinViewer.clearDistanceRepresentations();
            // Reset button text
            const showDistancesBtn = document.getElementById('show-distances-btn');
            if (showDistancesBtn) {
                showDistancesBtn.textContent = 'Show All Distances';
            }
        });
        
        // Sort mode selector handler
        const sortSelector = document.getElementById('sort-mode');
        if (sortSelector) {
            sortSelector.addEventListener('change', (event) => {
                this.setSortMode(event.target.value);
            });
        }
        
        // Toggle DNA button handler
        const toggleDNABtn = document.getElementById('toggle-dna-btn');
        if (toggleDNABtn) {
            toggleDNABtn.addEventListener('click', () => {
                const isShowing = this.proteinViewer.showingDNA;
                this.proteinViewer.toggleDNADisplay(!isShowing);
                toggleDNABtn.textContent = isShowing ? 'Show DNA' : 'Hide DNA';
            });
        }
        
        // Toggle all distances button handler
        const showDistancesBtn = document.getElementById('show-distances-btn');
        if (showDistancesBtn) {
            showDistancesBtn.addEventListener('click', () => {
                if (this.distanceMap) {
                    const isShowing = this.proteinViewer.toggleAllDistances(this.variants, this.distanceMap);
                    showDistancesBtn.textContent = isShowing ? 'Hide All Distances' : 'Show All Distances';
                }
            });
        }
        
        // Distance filter handler
        const distanceFilter = document.getElementById('distance-filter');
        if (distanceFilter) {
            distanceFilter.addEventListener('change', (event) => {
                this.filterVariantsByDistance(event.target.value);
            });
        }
    }
    
    filterVariantsByDistance(filterValue) {
        const listItems = document.querySelectorAll('#variant-list li');
        
        listItems.forEach(item => {
            if (item.classList.contains('disabled')) return;
            
            const variant = JSON.parse(item.dataset.variant);
            const distance = variant.distanceToDNA;
            
            let shouldShow = true;
            switch(filterValue) {
                case 'close':
                    shouldShow = distance !== null && distance < 5;
                    break;
                case 'medium':
                    shouldShow = distance !== null && distance >= 5 && distance < 10;
                    break;
                case 'far':
                    shouldShow = distance !== null && distance >= 10;
                    break;
                case 'all':
                default:
                    shouldShow = true;
            }
            
            item.style.display = shouldShow ? 'flex' : 'none';
        });
    }
}