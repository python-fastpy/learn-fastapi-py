"""The WorkflowDef shape, shared by lessons 10 and 12.

Not a lesson itself. Lesson 10 parses this from real markdown files;
lesson 12 builds the same shape directly as Python literals (no file I/O,
so the orchestration demo runs with nothing to set up). Previously each
lesson declared its own copy of this dataclass -- one here instead.
"""

from dataclasses import dataclass, field

import yaml


@dataclass
class WorkflowDef:
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    trigger_patterns: list[str] = field(default_factory=list)
    content: str = ""   # only lesson 10 (file-based) ever populates this

    @classmethod
    def from_markdown(cls, text: str) -> "WorkflowDef":
        """Split '---\\nYAML\\n---\\nmarkdown' into the contract and the steps."""
        if not text.startswith("---"):
            raise ValueError("workflow must start with YAML frontmatter (---)")
        _, frontmatter, content = text.split("---", 2)
        meta = yaml.safe_load(frontmatter)
        return cls(content=content.strip(), **meta)
