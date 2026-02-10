"""ErrorCanon JSON Schema definition and validation."""

ERRORCANON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "schema_version",
        "id",
        "url",
        "error",
        "environment",
        "verdict",
        "dead_ends",
        "workarounds",
        "transition_graph",
        "metadata",
    ],
    "properties": {
        "schema_version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "id": {
            "type": "string",
            "pattern": r"^[a-z0-9-]+/[a-z0-9-]+/[a-z0-9._-]+$",
        },
        "url": {"type": "string", "format": "uri"},
        "error": {
            "type": "object",
            "required": ["signature", "regex", "domain", "category"],
            "properties": {
                "signature": {"type": "string", "minLength": 1},
                "regex": {"type": "string", "minLength": 1},
                "domain": {
                    "type": "string",
                    "enum": [
                        "python",
                        "cuda",
                        "node",
                        "pip",
                        "docker",
                        "git",
                        "mcp",
                        "http",
                        "auth",
                        "db",
                        "rust",
                        "llm",
                    ],
                },
                "category": {"type": "string", "minLength": 1},
                "first_seen": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                "last_confirmed": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
            },
        },
        "environment": {
            "type": "object",
            "required": ["runtime", "os"],
            "properties": {
                "runtime": {
                    "type": "object",
                    "required": ["name", "version_range"],
                    "properties": {
                        "name": {"type": "string"},
                        "version_range": {"type": "string"},
                    },
                },
                "hardware": {"type": "object"},
                "os": {"type": "string"},
                "python": {"type": "string"},
                "additional": {"type": "object"},
            },
        },
        "verdict": {
            "type": "object",
            "required": [
                "resolvable",
                "fix_success_rate",
                "confidence",
                "last_updated",
                "summary",
            ],
            "properties": {
                "resolvable": {"type": "string", "enum": ["true", "partial", "false"]},
                "fix_success_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "last_updated": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                "summary": {"type": "string", "minLength": 1},
            },
        },
        "dead_ends": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["action", "why_fails", "fail_rate"],
                "properties": {
                    "action": {"type": "string", "minLength": 1},
                    "why_fails": {"type": "string", "minLength": 1},
                    "fail_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "condition": {"type": "string"},
                    "common_misconception": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "workarounds": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "required": ["action", "success_rate"],
                "properties": {
                    "action": {"type": "string", "minLength": 1},
                    "how": {"type": "string"},
                    "success_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "tradeoff": {"type": "string"},
                    "condition": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "transition_graph": {
            "type": "object",
            "required": ["leads_to", "preceded_by", "frequently_confused_with"],
            "properties": {
                "leads_to": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["error_id", "probability"],
                        "properties": {
                            "error_id": {"type": "string"},
                            "probability": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                            },
                            "condition": {"type": "string"},
                            "typical_delay": {"type": "string"},
                        },
                    },
                },
                "preceded_by": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["error_id", "probability"],
                        "properties": {
                            "error_id": {"type": "string"},
                            "probability": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                            },
                            "condition": {"type": "string"},
                        },
                    },
                },
                "frequently_confused_with": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["error_id", "distinction"],
                        "properties": {
                            "error_id": {"type": "string"},
                            "distinction": {"type": "string"},
                        },
                    },
                },
            },
        },
        "metadata": {
            "type": "object",
            "required": ["generated_by", "generation_date", "review_status", "evidence_count"],
            "properties": {
                "generated_by": {"type": "string"},
                "generation_date": {"type": "string"},
                "review_status": {
                    "type": "string",
                    "enum": ["auto_generated", "human_reviewed", "community_verified"],
                },
                "evidence_count": {"type": "integer", "minimum": 0},
                "page_views": {"type": "integer", "minimum": 0},
                "ai_agent_hits": {"type": "integer", "minimum": 0},
                "human_hits": {"type": "integer", "minimum": 0},
                "last_verification": {"type": "string"},
            },
        },
    },
}
