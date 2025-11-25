import json
import argparse
from collections import defaultdict
from pathlib import Path


def load_trivy_json(file_path):
    """Load uploaded Trivy JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_sbom(trivy):
    """Convert raw Trivy output into formatted SBOM JSON."""

    results = trivy.get("Results", [])
    component_map = {}
    severity_count = defaultdict(int)

    # New: store only highest-CVSS vulnerability per component
    highest_vuln_per_component = {}

    # Process each result entry
    for result in results:
        packages = result.get("Packages", [])
        vulns = result.get("Vulnerabilities", [])

        # Extract components (libraries)
        for pkg in packages:
            name = pkg.get("Name")
            version = pkg.get("Version", "unknown")

            component_map.setdefault(name, {
                "version": version,
                "license": "unknown",
                "vulnerabilities": []
            })

        # Extract vulnerabilities
        for v in vulns:
            comp = v.get("PkgName")
            severity = v.get("Severity", "none").lower()

            cvss_score = v.get("CVSS", {}).get("nvd", {}).get("V3Score", 0)

            # Count severity totals
            if severity in ["critical", "high", "medium", "low"]:
                severity_count[severity] += 1

            # Keep only highest CVSS vulnerability per component
            existing = highest_vuln_per_component.get(comp)
            if existing is None or cvss_score > existing["cvss"]:
                highest_vuln_per_component[comp] = {
                    "id": v.get("VulnerabilityID"),
                    "severity": severity,
                    "component": comp,
                    "description": v.get("Description", ""),
                    "cvss": cvss_score,
                    "status": v.get("Status", "unknown"),
                    "discoveredDate": v.get("PublishedDate", "")
                }

            # Add to component’s list for severity calculation
            if comp in component_map:
                component_map[comp]["vulnerabilities"].append(v)

    # Prepare SBOM component structure
    severity_rank = ["none", "low", "medium", "high", "critical"]
    components_output = []

    for name, info in component_map.items():
        vulns = info["vulnerabilities"]

        if vulns:
            highest_severity = max(
                [v.get("Severity", "none").lower() for v in vulns],
                key=lambda s: severity_rank.index(s)
            )
        else:
            highest_severity = "none"

        components_output.append({
            "name": name,
            "version": info["version"],
            "license": info["license"],
            "vulnerabilities": len(vulns),
            "severity": highest_severity,
            "type": "library"
        })

    # Build final SBOM JSON
    sbom_output = {
        "sbom": {
            "totalComponents": len(components_output),
            "criticalVulnerabilities": severity_count["critical"],
            "highVulnerabilities": severity_count["high"],
            "mediumVulnerabilities": severity_count["medium"],
            "lowVulnerabilities": severity_count["low"],
            "components": components_output
        },

        # NEW: Only highest CVSS vulnerability for each component
        "vulnerabilityLibrary": list(highest_vuln_per_component.values())
    }

    return sbom_output


def main():
    parser = argparse.ArgumentParser(description="Generate SBOM from Trivy JSON.")
    parser.add_argument("--input", required=True, help="Path to uploaded Trivy JSON file")
    parser.add_argument("--output", default="sbom_output.json", help="Where to save SBOM JSON")
    args = parser.parse_args()

    print(f"📄 Reading input JSON: {args.input}")
    trivy = load_trivy_json(args.input)

    print("⚙️  Processing and generating SBOM...")
    sbom = generate_sbom(trivy)

    # Save output JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)

    print(f"✅ SBOM generated successfully!")
    print(f"📦 Output saved at: {args.output}")


if __name__ == "__main__":
    main()
