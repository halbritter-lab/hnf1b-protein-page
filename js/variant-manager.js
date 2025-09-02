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
            
            // Format distance display with atom details
            let distanceDisplay = '';
            if (this.distanceMap && residueExists) {
                const distanceInfo = this.distanceMap.get(variant.residue);
                if (distanceInfo) {
                    const distance = distanceInfo.distance;
                    const category = this.getDistanceCategory(distance);
                    const atomName = distanceInfo.residueAtom ? distanceInfo.residueAtom.atomname : 'CA';
                    const measurementNote = distanceInfo.measurementType === 'closest-atom' ? 
                        ` (${atomName} atom)` : ' (CA atom)';
                    distanceDisplay = `<small class="distance-info distance-${category}">Distance to DNA: ${distance.toFixed(1)}Å${measurementNote}</small>`;
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
        
        // Representation controls handlers
        this.initializeRepresentationHandlers();
    }
    
    initializeRepresentationHandlers() {
        // Representation selector handler
        const repSelect = document.getElementById('representation-select');
        if (repSelect) {
            repSelect.addEventListener('change', (event) => {
                const loadingIndicator = document.querySelector('.representation-loading');
                const infoDiv = document.getElementById('representation-info');
                const opacitySlider = document.getElementById('opacity-slider');
                const opacityValue = document.getElementById('opacity-value');
                
                // Show loading indicator
                if (loadingIndicator) {
                    loadingIndicator.classList.add('active');
                }
                
                // Auto-adjust opacity for surface representation
                if (event.target.value === 'surface' && opacitySlider && opacitySlider.value > 70) {
                    // Set surface to 70% opacity by default for better visibility
                    opacitySlider.value = 70;
                    if (opacityValue) {
                        opacityValue.textContent = '70%';
                    }
                    this.proteinViewer.updateOpacity(70);
                }
                
                // Change representation
                this.proteinViewer.changeRepresentation(event.target.value);
                
                // Update info text
                if (infoDiv && this.proteinViewer.representationManager) {
                    const repInfo = this.proteinViewer.representationManager.representations[event.target.value];
                    if (repInfo) {
                        infoDiv.textContent = repInfo.description;
                        infoDiv.style.display = 'block';
                    }
                }
                
                // Update sidechain checkbox state
                this.updateSidechainState(event.target.value);
                
                // Hide loading indicator after a short delay
                setTimeout(() => {
                    if (loadingIndicator) {
                        loadingIndicator.classList.remove('active');
                    }
                }, 500);
            });
        }
        
        // Color scheme selector handler
        const colorSchemeSelect = document.getElementById('color-scheme');
        if (colorSchemeSelect) {
            colorSchemeSelect.addEventListener('change', (event) => {
                this.proteinViewer.updateColorScheme(event.target.value);
            });
        }
        
        // Opacity slider handler
        const opacitySlider = document.getElementById('opacity-slider');
        const opacityValue = document.getElementById('opacity-value');
        if (opacitySlider) {
            opacitySlider.addEventListener('input', (event) => {
                const value = event.target.value;
                if (opacityValue) {
                    opacityValue.textContent = `${value}%`;
                }
                this.proteinViewer.updateOpacity(value);
            });
        }
        
        // Sidechain checkbox handler
        const sidechainCheckbox = document.getElementById('show-sidechains');
        if (sidechainCheckbox) {
            sidechainCheckbox.addEventListener('change', (event) => {
                this.proteinViewer.toggleSidechains(event.target.checked);
            });
        }
    }
    
    updateSidechainState(representationType) {
        const sidechainGroup = document.getElementById('sidechain-group');
        const sidechainCheckbox = document.getElementById('show-sidechains');
        
        if (sidechainGroup && this.proteinViewer.representationManager) {
            const supportsSidechains = this.proteinViewer.representationManager.supportsSidechains(representationType);
            
            if (supportsSidechains) {
                sidechainGroup.classList.remove('disabled');
            } else {
                sidechainGroup.classList.add('disabled');
                if (sidechainCheckbox) {
                    sidechainCheckbox.checked = false;
                    this.proteinViewer.toggleSidechains(false);
                }
            }
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