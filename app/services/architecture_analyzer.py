# app/services/architecture_analyzer.py
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Configure logging for architecture analysis
logging.basicConfig(level=logging.INFO)
arch_logger = logging.getLogger("architecture_analyzer")


class ArchitectureAnalyzer:
    """
    Analyzes project architecture patterns and generates dependency diagrams.
    """

    def __init__(self):
        self.patterns = {
            "mvc": ["models", "views", "controllers"],
            "mvp": ["models", "views", "presenters"],
            "mvvm": ["models", "views", "viewmodels"],
            "layered": ["presentation", "business", "data", "persistence"],
            "microservices": ["services", "api", "gateway"],
            "clean_architecture": ["entities", "use_cases", "adapters", "frameworks"],
            "hexagonal": ["domain", "ports", "adapters"],
            "repository": ["repositories", "models", "entities"],
            "service_layer": ["services", "handlers", "domain"],
        }

    def analyze_architecture_patterns(
        self, files_content: Dict[str, str], ast_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the project for common architectural patterns.

        Args:
            files_content: Dictionary of file paths and their content
            ast_data: AST analysis data

        Returns:
            Dictionary containing detected patterns and architecture info
        """
        arch_logger.info("🏗️ Starting architecture pattern analysis")

        analysis = {
            "detected_patterns": [],
            "directory_structure": self._analyze_directory_structure(files_content),
            "dependencies": self._analyze_dependencies(files_content, ast_data),
            "layers": self._identify_layers(files_content),
            "components": self._identify_components(files_content, ast_data),
            "data_flow": self._analyze_data_flow(files_content, ast_data),
        }

        # Detect architectural patterns
        for pattern_name, pattern_keywords in self.patterns.items():
            if self._detect_pattern(files_content, pattern_keywords):
                analysis["detected_patterns"].append(
                    {
                        "name": pattern_name,
                        "confidence": self._calculate_pattern_confidence(
                            files_content, pattern_keywords
                        ),
                        "evidence": self._get_pattern_evidence(
                            files_content, pattern_keywords
                        ),
                    }
                )

        arch_logger.info(
            f"🔍 Detected {len(analysis['detected_patterns'])} architectural patterns"
        )
        return analysis

    def _analyze_directory_structure(
        self, files_content: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """Analyze the directory structure of the project."""
        structure = {}

        for filepath in files_content.keys():
            parts = filepath.split("/")
            if len(parts) > 1:
                directory = parts[0]
                if directory not in structure:
                    structure[directory] = []
                structure[directory].append("/".join(parts[1:]))

        return structure

    def _analyze_dependencies(
        self, files_content: Dict[str, str], ast_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Analyze dependencies between modules and files."""
        dependencies = {}

        for filepath, content in files_content.items():
            file_deps = []

            # Extract imports from Python files
            if filepath.endswith(".py"):
                import_patterns = [
                    r"from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import",
                    r"import\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
                ]

                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Filter out standard library imports
                        if not self._is_standard_library(match):
                            file_deps.append(match)

            # Extract imports from JavaScript/TypeScript files
            elif filepath.endswith((".js", ".ts", ".jsx", ".tsx")):
                import_patterns = [
                    r'import.*from\s+[\'"]([^\'\"]+)[\'"]',
                    r'require\([\'"]([^\'\"]+)[\'"]\)',
                ]

                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    file_deps.extend(matches)

            if file_deps:
                dependencies[filepath] = list(set(file_deps))

        return dependencies

    def _identify_layers(self, files_content: Dict[str, str]) -> List[Dict[str, Any]]:
        """Identify architectural layers in the project."""
        layers = []

        # Common layer patterns
        layer_patterns = {
            "presentation": ["ui", "views", "templates", "frontend", "web", "api"],
            "business": ["services", "business", "logic", "domain", "core"],
            "data": ["data", "repositories", "dao", "models", "entities"],
            "infrastructure": ["infrastructure", "config", "utils", "helpers"],
        }

        for layer_name, keywords in layer_patterns.items():
            layer_files = []
            for filepath in files_content.keys():
                if any(keyword in filepath.lower() for keyword in keywords):
                    layer_files.append(filepath)

            if layer_files:
                layers.append(
                    {
                        "name": layer_name,
                        "files": layer_files,
                        "file_count": len(layer_files),
                    }
                )

        return layers

    def _identify_components(
        self, files_content: Dict[str, str], ast_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify main components/modules in the project."""
        components = []

        # Group files by directory
        directories = {}
        for filepath in files_content.keys():
            parts = filepath.split("/")
            if len(parts) > 1:
                dir_name = parts[0]
                if dir_name not in directories:
                    directories[dir_name] = []
                directories[dir_name].append(filepath)

        for dir_name, files in directories.items():
            # Skip common non-component directories
            if dir_name.lower() in ["__pycache__", ".git", "node_modules", "venv"]:
                continue

            component = {
                "name": dir_name,
                "files": files,
                "file_count": len(files),
                "types": self._get_file_types(files),
                "main_functions": [],
                "main_classes": [],
            }

            # Extract main functions and classes from AST data
            if ast_data.get("file_details"):
                for filepath in files:
                    if filepath in ast_data["file_details"]:
                        details = ast_data["file_details"][filepath]
                        if details.get("functions"):
                            component["main_functions"].extend(
                                [f["name"] for f in details["functions"][:3]]
                            )
                        if details.get("classes"):
                            component["main_classes"].extend(
                                [c["name"] for c in details["classes"][:3]]
                            )

            components.append(component)

        return components

    def _analyze_data_flow(
        self, files_content: Dict[str, str], ast_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Analyze data flow patterns in the project."""
        flows = []

        # Look for common data flow patterns
        flow_patterns = [
            {
                "from": "api",
                "to": "service",
                "pattern": r"(api|router|controller).*service",
            },
            {"from": "service", "to": "repository", "pattern": r"service.*repository"},
            {
                "from": "repository",
                "to": "database",
                "pattern": r"repository.*(db|database|model)",
            },
            {"from": "controller", "to": "view", "pattern": r"controller.*view"},
            {"from": "model", "to": "view", "pattern": r"model.*view"},
        ]

        for filepath, content in files_content.items():
            for flow_pattern in flow_patterns:
                if re.search(flow_pattern["pattern"], content, re.IGNORECASE):
                    flows.append(
                        {
                            "from": flow_pattern["from"],
                            "to": flow_pattern["to"],
                            "file": filepath,
                        }
                    )

        return flows

    def _detect_pattern(
        self, files_content: Dict[str, str], pattern_keywords: List[str]
    ) -> bool:
        """Detect if a specific architectural pattern is present."""
        found_keywords = 0

        for filepath in files_content.keys():
            filepath_lower = filepath.lower()
            for keyword in pattern_keywords:
                if keyword in filepath_lower:
                    found_keywords += 1
                    break

        # Pattern is detected if at least 2 keywords are found
        return found_keywords >= 2

    def _calculate_pattern_confidence(
        self, files_content: Dict[str, str], pattern_keywords: List[str]
    ) -> float:
        """Calculate confidence score for a detected pattern."""
        total_files = len(files_content)
        matching_files = 0

        for filepath in files_content.keys():
            filepath_lower = filepath.lower()
            if any(keyword in filepath_lower for keyword in pattern_keywords):
                matching_files += 1

        return min(matching_files / max(len(pattern_keywords), 1), 1.0)

    def _get_pattern_evidence(
        self, files_content: Dict[str, str], pattern_keywords: List[str]
    ) -> List[str]:
        """Get evidence files for a detected pattern."""
        evidence = []

        for filepath in files_content.keys():
            filepath_lower = filepath.lower()
            for keyword in pattern_keywords:
                if keyword in filepath_lower:
                    evidence.append(filepath)
                    break

        return evidence[:5]  # Limit to 5 evidence files

    def _get_file_types(self, files: List[str]) -> Dict[str, int]:
        """Get file type distribution for a list of files."""
        types = {}

        for filepath in files:
            ext = Path(filepath).suffix.lower()
            if ext:
                types[ext] = types.get(ext, 0) + 1

        return types

    def _is_standard_library(self, module_name: str) -> bool:
        """Check if a module is part of Python standard library."""
        standard_libs = {
            "os",
            "sys",
            "json",
            "datetime",
            "time",
            "random",
            "math",
            "collections",
            "itertools",
            "functools",
            "operator",
            "re",
            "string",
            "io",
            "pathlib",
            "logging",
            "unittest",
            "typing",
            "dataclasses",
            "enum",
            "abc",
            "copy",
            "pickle",
            "csv",
            "xml",
            "html",
            "urllib",
            "http",
            "email",
            "base64",
            "hashlib",
            "hmac",
            "secrets",
            "ssl",
            "socket",
            "threading",
            "multiprocessing",
            "asyncio",
            "concurrent",
            "queue",
            "subprocess",
            "shutil",
            "tempfile",
            "glob",
            "fnmatch",
            "linecache",
            "textwrap",
            "unicodedata",
            "stringprep",
            "readline",
            "rlcompleter",
            "pprint",
            "reprlib",
            "locale",
            "gettext",
            "argparse",
            "optparse",
            "configparser",
            "fileinput",
            "calendar",
            "cmd",
            "shlex",
            "tkinter",
            "turtle",
            "sqlite3",
            "zlib",
            "gzip",
            "bz2",
            "lzma",
            "zipfile",
            "tarfile",
        }

        root_module = module_name.split(".")[0]
        return root_module in standard_libs

    def generate_architecture_diagrams(
        self, analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate Mermaid diagrams for the analyzed architecture.

        Args:
            analysis: Architecture analysis results

        Returns:
            Dictionary containing different types of diagrams
        """
        arch_logger.info("📊 Generating architecture diagrams")

        diagrams = {}

        # Generate component diagram
        if analysis.get("components"):
            diagrams["component_diagram"] = self._generate_component_diagram(
                analysis["components"]
            )

        # Generate dependency diagram
        if analysis.get("dependencies"):
            diagrams["dependency_diagram"] = self._generate_dependency_diagram(
                analysis["dependencies"]
            )

        # Generate layer diagram
        if analysis.get("layers"):
            diagrams["layer_diagram"] = self._generate_layer_diagram(analysis["layers"])

        # Generate data flow diagram
        if analysis.get("data_flow"):
            diagrams["data_flow_diagram"] = self._generate_data_flow_diagram(
                analysis["data_flow"]
            )

        arch_logger.info(f"📈 Generated {len(diagrams)} architecture diagrams")
        return diagrams

    def _generate_component_diagram(self, components: List[Dict[str, Any]]) -> str:
        """Generate a Mermaid component diagram."""
        diagram = "graph TB\n"

        for component in components[:8]:  # Limit to 8 components for readability
            comp_name = component["name"].replace("-", "_").replace(".", "_")
            file_count = component["file_count"]

            diagram += (
                f'    {comp_name}["{component["name"]}<br/>({file_count} files)"]\n'
            )

            # Add connections based on common patterns
            if "api" in component["name"].lower():
                diagram += f"    User --> {comp_name}\n"
            elif "service" in component["name"].lower():
                diagram += f"    {comp_name} --> Database\n"

        return diagram

    def _generate_dependency_diagram(self, dependencies: Dict[str, List[str]]) -> str:
        """Generate a Mermaid dependency diagram."""
        diagram = "graph LR\n"

        # Limit to most connected files
        sorted_deps = sorted(
            dependencies.items(), key=lambda x: len(x[1]), reverse=True
        )[:10]

        for filepath, deps in sorted_deps:
            file_name = Path(filepath).stem.replace("-", "_").replace(".", "_")

            for dep in deps[:3]:  # Limit to 3 dependencies per file
                dep_name = dep.replace(".", "_").replace("-", "_")
                diagram += f"    {file_name} --> {dep_name}\n"

        return diagram

    def _generate_layer_diagram(self, layers: List[Dict[str, Any]]) -> str:
        """Generate a Mermaid layer architecture diagram."""
        diagram = "graph TD\n"

        # Sort layers by typical architecture order
        layer_order = {"presentation": 1, "business": 2, "data": 3, "infrastructure": 4}
        sorted_layers = sorted(layers, key=lambda x: layer_order.get(x["name"], 5))

        prev_layer = None
        for layer in sorted_layers:
            layer_name = layer["name"].replace("-", "_")
            file_count = layer["file_count"]

            diagram += f'    {layer_name}["{layer["name"].title()} Layer<br/>({file_count} files)"]\n'

            if prev_layer:
                diagram += f"    {prev_layer} --> {layer_name}\n"

            prev_layer = layer_name

        return diagram

    def _generate_data_flow_diagram(self, data_flows: List[Dict[str, str]]) -> str:
        """Generate a Mermaid data flow diagram."""
        diagram = "graph LR\n"

        # Group flows by from-to pairs
        flow_counts = {}
        for flow in data_flows:
            key = (flow["from"], flow["to"])
            flow_counts[key] = flow_counts.get(key, 0) + 1

        # Generate diagram for most common flows
        for (from_comp, to_comp), count in sorted(
            flow_counts.items(), key=lambda x: x[1], reverse=True
        )[:8]:
            from_name = from_comp.replace("-", "_").title()
            to_name = to_comp.replace("-", "_").title()

            diagram += f'    {from_name} -->|"{count} connections"| {to_name}\n'

        return diagram
