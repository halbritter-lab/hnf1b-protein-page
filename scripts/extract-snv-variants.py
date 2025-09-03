"""Module for extracting SNV variants from CSV and
generating JavaScript file."""
import csv
import re


def extract_snv_variants(csv_file):
    """Extract SNV variants from CSV file and format them for variants.js"""
    variants = []
    seen_variants = set()  # Track unique variants to avoid duplicates

    # Valid three-letter amino acid codes for validation
    valid_three_letter = {
        'Ala', 'Cys', 'Asp', 'Glu', 'Phe', 'Gly', 'His', 'Ile',
        'Lys', 'Leu', 'Met', 'Asn', 'Pro', 'Gln', 'Arg', 'Ser',
        'Thr', 'Val', 'Trp', 'Tyr', 'Ter'
    }

    # Amino acid conversion dictionaries
    single_to_three = {
        'A': 'Ala', 'C': 'Cys', 'D': 'Asp', 'E': 'Glu', 'F': 'Phe',
        'G': 'Gly', 'H': 'His', 'I': 'Ile', 'K': 'Lys', 'L': 'Leu',
        'M': 'Met', 'N': 'Asn', 'P': 'Pro', 'Q': 'Gln', 'R': 'Arg',
        'S': 'Ser', 'T': 'Thr', 'V': 'Val', 'W': 'Trp', 'Y': 'Tyr',
        '*': 'Ter', 'X': 'Ter'  # Stop codons
    }

    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # Only process SNV variant types
            if row['VariantType'] != 'SNV':
                continue

            # Use Varisome column for protein variant extraction
            varisome_data = row.get('Varsome', '')
            if not varisome_data:
                # Fallback to VariantReported if Varisome is empty
                varisome_data = row.get('VariantReported', '')
                if not varisome_data:
                    continue

            # Extract protein variant from Varisome format:
            # HNF1B(NM_000458.4):c.###X>X (p.XxxYyyZzz)
            # Pattern to extract protein variant from parentheses
            protein_in_parens = r'\(p\.([^)]+)\)'
            match = re.search(protein_in_parens, varisome_data)

            if match:
                protein_variant = 'p.' + match.group(1)
                # Parse the extracted protein variant
                # Try three-letter code pattern (p.Xxx###Xxx)
                protein_pattern_three = (
                    r'p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2}|Ter|\*)'
                )
                match = re.search(protein_pattern_three, protein_variant)

                if match:
                    ref_aa = match.group(1)
                    position = int(match.group(2))
                    alt_aa = match.group(3)
                else:
                    # Try single-letter code pattern (p.X###X)
                    protein_pattern_single = r'p\.([A-Z])(\d+)([A-Z\*])'
                    match = re.search(protein_pattern_single, protein_variant)

                    if match:
                        ref_aa_single = match.group(1)
                        position = int(match.group(2))
                        alt_aa_single = match.group(3)

                        ref_aa = single_to_three.get(
                            ref_aa_single, ref_aa_single
                        )
                        alt_aa = single_to_three.get(
                            alt_aa_single, alt_aa_single
                        )
                    else:
                        continue
            else:
                # Fallback: Try to extract directly without parentheses
                # Try three-letter code pattern first (p.Xxx###Xxx)
                protein_pattern_three = (
                    r'p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2}|Ter|\*)'
                )
                match = re.search(protein_pattern_three, varisome_data)

                if match:
                    ref_aa = match.group(1)
                    position = int(match.group(2))
                    alt_aa = match.group(3)
                else:
                    # Try single-letter code pattern (p.X###X)
                    protein_pattern_single = r'p\.([A-Z])(\d+)([A-Z\*])'
                    match = re.search(protein_pattern_single, varisome_data)

                    if match:
                        ref_aa_single = match.group(1)
                        position = int(match.group(2))
                        alt_aa_single = match.group(3)

                        ref_aa = single_to_three.get(
                            ref_aa_single, ref_aa_single
                        )
                        alt_aa = single_to_three.get(
                            alt_aa_single, alt_aa_single
                        )
                    else:
                        continue

            # Validate the parsed variant
            if (ref_aa not in valid_three_letter or
                    alt_aa not in valid_three_letter):
                continue

            # Format variant name in three-letter code
            variant_name = f'p.{ref_aa}{position}{alt_aa}'

            # Skip if we've already seen this variant
            if variant_name in seen_variants:
                continue
            seen_variants.add(variant_name)

            # Determine pathogenicity classification and color
            classification = row.get(
                'verdict_classification', 'Uncertain Significance'
            )

            # Map classification to color
            if classification == 'Pathogenic':
                color = 'red'
                type_label = 'Pathogenic'
            elif classification == 'Likely Pathogenic':
                color = 'orange'
                type_label = 'Likely Pathogenic'
            elif classification == 'Benign':
                color = 'green'
                type_label = 'Benign'
            elif classification == 'Likely Benign':
                color = '#f5d547'
                type_label = 'Likely Benign'
            else:  # Uncertain Significance or unknown
                color = 'grey'
                type_label = 'Uncertain Significance'

            # Skip termination variants (nonsense variants)
            # These are typically removed by nonsense-mediated decay
            if alt_aa == 'Ter':
                continue

            # Create variant object
            variant = {
                'name': variant_name,
                'residue': position,
                'type': type_label,
                'color': color,
                'distanceToDNA': None,
                'closestDNAAtom': None
            }

            variants.append(variant)

    # Sort variants by residue position
    variants.sort(key=lambda x: x['residue'])

    return variants


def generate_js_file(variants, unparsed_variants=None):
    """Generate JavaScript file with optional unparsed variants."""
    js_content = (
        "// Variant data configuration\n"
        "// Note: distanceToDNA and closestDNAAtom will be populated "
        "dynamically by DistanceCalculator\n"
        "export const variants = [\n"
    )

    for i, variant in enumerate(variants):
        js_content += (
            f"    {{ name: '{variant['name']}', "
            f"residue: {variant['residue']}, "
            f"type: '{variant['type']}', "
            f"color: '{variant['color']}', "
            f"distanceToDNA: null, "
            f"closestDNAAtom: null }}"
        )
        if i < len(variants) - 1:
            js_content += ",\n"
        else:
            js_content += "\n"

    js_content += "];\n"

    # Add unparsed variants as a commented section if provided
    if unparsed_variants:
        js_content += "\n// UNPARSED VARIANTS FROM CSV\n"
        js_content += (
            "// These variants could not be automatically converted "
            "to protein notation (p. format)\n"
        )
        js_content += (
            "// They are preserved here for reference and "
            "potential manual conversion\n"
        )
        js_content += (
            "// Total unparsed: " + str(len(unparsed_variants)) + "\n"
        )
        js_content += "/*\n"
        js_content += "const unparsedVariants = [\n"

        # Group variants by type for better organization
        cdna_variants = [v for v in unparsed_variants if v.startswith('c.')]
        ivs_variants = [v for v in unparsed_variants if 'IVS' in v.upper()]
        other_variants = [
            v for v in unparsed_variants
            if not v.startswith('c.') and 'IVS' not in v.upper()
        ]

        if cdna_variants:
            js_content += "  // cDNA notation variants (c.)\n"
            for variant in sorted(cdna_variants):
                js_content += f"  '{variant}',\n"

        if ivs_variants:
            js_content += "  // Intronic variants (IVS)\n"
            for variant in sorted(ivs_variants):
                js_content += f"  '{variant}',\n"

        if other_variants:
            js_content += "  // Other variants\n"
            for variant in sorted(other_variants):
                js_content += f"  '{variant}',\n"

        js_content += "];\n"
        js_content += "*/\n"

    return js_content


def extract_snv_variants_with_logging(csv_file):
    """Extract SNV variants and log any that couldn't be parsed."""
    variants = []
    seen_variants = set()
    unparsed_variants = []

    # Valid three-letter amino acid codes for validation
    valid_three_letter = {
        'Ala', 'Cys', 'Asp', 'Glu', 'Phe', 'Gly', 'His', 'Ile',
        'Lys', 'Leu', 'Met', 'Asn', 'Pro', 'Gln', 'Arg', 'Ser',
        'Thr', 'Val', 'Trp', 'Tyr', 'Ter'
    }

    # Amino acid conversion dictionaries
    single_to_three = {
        'A': 'Ala', 'C': 'Cys', 'D': 'Asp', 'E': 'Glu', 'F': 'Phe',
        'G': 'Gly', 'H': 'His', 'I': 'Ile', 'K': 'Lys', 'L': 'Leu',
        'M': 'Met', 'N': 'Asn', 'P': 'Pro', 'Q': 'Gln', 'R': 'Arg',
        'S': 'Ser', 'T': 'Thr', 'V': 'Val', 'W': 'Trp', 'Y': 'Tyr',
        '*': 'Ter', 'X': 'Ter'
    }

    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row['VariantType'] != 'SNV':
                continue

            # Prioritize Varisome column for accurate extraction
            varisome_data = row.get('Varsome', '')
            variant_reported = row.get('VariantReported', '')

            # Always prioritize Varisome if it contains protein variant
            if 'p.' in varisome_data:
                source_data = varisome_data
            elif varisome_data:
                source_data = varisome_data
            else:
                # Only use VariantReported if Varisome is empty
                source_data = variant_reported

            if not source_data:
                continue

            parsed = False
            ref_aa = None
            position = None
            alt_aa = None

            # Extract protein variant from Varisome format:
            # HNF1B(NM_000458.4):c.###X>X (p.XxxYyyZzz)
            protein_in_parens = r'\(p\.([^)]+)\)'
            match = re.search(protein_in_parens, source_data)

            if match:
                protein_variant = 'p.' + match.group(1)
                # Parse the extracted protein variant
                # Try three-letter code pattern (p.Xxx###Xxx)
                protein_pattern_three = (
                    r'p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2}|Ter|\*|X)'
                )
                match = re.search(protein_pattern_three, protein_variant)

                if match:
                    ref_aa = match.group(1)
                    position = int(match.group(2))
                    alt_aa = match.group(3)
                    if alt_aa == 'X':
                        alt_aa = 'Ter'
                    parsed = True
                else:
                    # Try single-letter code pattern (p.X###X)
                    protein_pattern_single = r'p\.([A-Z])(\d+)([A-Z\*X])'
                    match = re.search(protein_pattern_single, protein_variant)

                    if match:
                        ref_aa_single = match.group(1)
                        position = int(match.group(2))
                        alt_aa_single = match.group(3)

                        ref_aa = single_to_three.get(
                            ref_aa_single, ref_aa_single
                        )
                        alt_aa = single_to_three.get(
                            alt_aa_single, alt_aa_single
                        )
                        parsed = True

            if not parsed:
                # Fallback: Try to extract directly without parentheses
                # Try three-letter code pattern first (p.Xxx###Xxx)
                protein_pattern_three = (
                    r'p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2}|Ter|\*|X)'
                )
                match = re.search(protein_pattern_three, source_data)

                if match:
                    ref_aa = match.group(1)
                    position = int(match.group(2))
                    alt_aa = match.group(3)
                    if alt_aa == 'X':
                        alt_aa = 'Ter'
                    parsed = True

            if not parsed:
                # Try single-letter code pattern with p. prefix (p.X###X)
                protein_pattern_single = r'p\.([A-Z])(\d+)([A-Z\*X])'
                match = re.search(protein_pattern_single, source_data)

                if match:
                    ref_aa_single = match.group(1)
                    position = int(match.group(2))
                    alt_aa_single = match.group(3)

                    ref_aa = single_to_three.get(ref_aa_single, ref_aa_single)
                    alt_aa = single_to_three.get(alt_aa_single, alt_aa_single)
                    parsed = True

            if not parsed:
                # Try single-letter code pattern without p. prefix (X###X)
                protein_pattern_simple = r'([A-Z])(\d+)([A-Z\*X])'
                # Avoid matching nucleotide changes like c.232G>T
                if not re.match(r'c\.', source_data):
                    match = re.search(
                        protein_pattern_simple, source_data
                    )

                    if match:
                        ref_aa_single = match.group(1)
                        position = int(match.group(2))
                        alt_aa_single = match.group(3)

                        # Skip if it looks like a nucleotide change
                        nucleotides = ['A', 'T', 'G', 'C']
                        if (ref_aa_single not in nucleotides or
                                alt_aa_single not in nucleotides):
                            ref_aa = single_to_three.get(
                                ref_aa_single, ref_aa_single
                            )
                            alt_aa = single_to_three.get(
                                alt_aa_single, alt_aa_single
                            )
                            parsed = True

            if not parsed:
                # Store the original data for logging
                unparsed_data = (
                    varisome_data if varisome_data
                    else variant_reported
                )
                unparsed_variants.append(unparsed_data)
                continue

            # Validate the parsed variant
            if (ref_aa not in valid_three_letter or
                    alt_aa not in valid_three_letter):
                unparsed_data = (
                    varisome_data if varisome_data
                    else variant_reported
                )
                unparsed_variants.append(unparsed_data)
                continue

            variant_name = f'p.{ref_aa}{position}{alt_aa}'

            if variant_name in seen_variants:
                continue
            seen_variants.add(variant_name)

            classification = row.get(
                'verdict_classification', 'Uncertain Significance'
            )

            if classification == 'Pathogenic':
                color = 'red'
                type_label = 'Pathogenic'
            elif classification == 'Likely Pathogenic':
                color = 'orange'
                type_label = 'Likely Pathogenic'
            elif classification == 'Benign':
                color = 'green'
                type_label = 'Benign'
            elif classification == 'Likely Benign':
                color = '#f5d547'
                type_label = 'Likely Benign'
            else:
                color = 'grey'
                type_label = 'Uncertain Significance'

            # Skip termination variants (nonsense variants)
            # These are typically removed by nonsense-mediated decay
            if alt_aa == 'Ter':
                # Store as unparsed for documentation
                unparsed_variants.append(
                    f"{variant_name} (termination variant)"
                )
                continue

            variant = {
                'name': variant_name,
                'residue': position,
                'type': type_label,
                'color': color,
                'distanceToDNA': None,
                'closestDNAAtom': None
            }

            variants.append(variant)

    variants.sort(key=lambda x: x['residue'])

    return variants, unparsed_variants


def main():
    """Main function to extract variants and generate JS file."""
    csv_file = '../data/HNF1B_DataCuration - Individuals.csv'
    output_file = '../js/variants.js'

    # Extract SNV variants with logging
    print("Extracting SNV variants from CSV...")
    variants, unparsed = extract_snv_variants_with_logging(csv_file)

    print(f"Found {len(variants)} unique SNV variants")

    if unparsed:
        print(
            f"\n⚠ Found {len(unparsed)} SNV variants "
            "that couldn't be parsed:"
        )
        for var in unparsed[:10]:  # Show first 10
            print(f"  - {var}")
        if len(unparsed) > 10:
            print(f"  ... and {len(unparsed) - 10} more")

    # Generate JavaScript file content with unparsed variants
    js_content = generate_js_file(variants, unparsed)

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(
        f"\nSuccessfully wrote {len(variants)} variants to {output_file}"
    )

    # Print summary statistics
    pathogenic_count = sum(
        1 for v in variants if v['type'] == 'Pathogenic'
    )
    likely_pathogenic_count = sum(
        1 for v in variants if v['type'] == 'Likely Pathogenic'
    )
    benign_count = sum(1 for v in variants if v['type'] == 'Benign')
    likely_benign_count = sum(
        1 for v in variants if v['type'] == 'Likely Benign'
    )
    uncertain_count = sum(
        1 for v in variants if v['type'] == 'Uncertain Significance'
    )

    print("\nVariant classification summary:")
    print(f"  Pathogenic: {pathogenic_count}")
    print(f"  Likely Pathogenic: {likely_pathogenic_count}")
    print(f"  Benign: {benign_count}")
    print(f"  Likely Benign: {likely_benign_count}")
    print(f"  Uncertain Significance: {uncertain_count}")


if __name__ == "__main__":
    main()

