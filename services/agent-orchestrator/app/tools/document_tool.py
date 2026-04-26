import io
import json
from typing import Any, Dict, List, Optional

class DocumentTool:
    name = "document_tool"
    description = "Parse documents and generate structured outputs"

    def __init__(self, **kwargs):
        pass

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            "parse_csv": self._parse_csv,
            "generate_json_report": self._generate_json_report,
            "extract_table": self._extract_table,
            "format_report": self._format_report,
        }
        fn = actions.get(action)
        if not fn:
            return {"error": f"Unknown action: {action}"}
        return await fn(**kwargs)

    async def _parse_csv(self, content: str, **kwargs) -> Dict[str, Any]:
        import csv
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        return {"rows": rows, "columns": reader.fieldnames or [], "count": len(rows)}

    async def _generate_json_report(self, data: Dict, title: str = "Report", **kwargs) -> Dict[str, Any]:
        return {"report": {"title": title, "data": data, "format": "json"}}

    async def _extract_table(self, text: str, **kwargs) -> Dict[str, Any]:
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        if not lines:
            return {"rows": [], "headers": []}
        headers = [h.strip() for h in lines[0].split("|") if h.strip()]
        rows = []
        for line in lines[2:]:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if cols:
                rows.append(dict(zip(headers, cols)))
        return {"headers": headers, "rows": rows}

    async def _format_report(self, sections: List[Dict], **kwargs) -> Dict[str, Any]:
        report = ""
        for section in sections:
            report += f"\n## {section.get('title', '')}\n\n{section.get('content', '')}\n"
        return {"report": report.strip(), "sections": len(sections)}

    def schema(self) -> Dict:
        return {"name": self.name, "description": self.description,
                "parameters": {"action": {"type": "string"}, "content": {"type": "string"}}}
