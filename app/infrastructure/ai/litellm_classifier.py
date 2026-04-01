import json
import os
import re
from datetime import datetime, timezone

from app.application.ports.classifier_port import ClassifierPort
from app.domain.constants.departments import (
    KNOWN_DEPARTMENTS,
    infer_department_from_text,
    normalize_department,
)
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority

try:
    from litellm import completion
except ImportError:
    completion = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LitellmClassifier(ClassifierPort):
    DEFAULT_MODEL = "azure_ai/gpt-oss-120b"

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
    ) -> None:
        self.model_name = model_name or os.getenv("LITELLM_MODEL", self.DEFAULT_MODEL)
        self.proxy_api_base = os.getenv("LITELLM_API_BASE") or os.getenv("OPENAI_BASE_URL")
        self.proxy_api_key = os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")

        self.api_key = (
            api_key
            or os.getenv("AZURE_API_KEY")
            or os.getenv("AZURE_AI_API_KEY")
            or self.proxy_api_key
        )
        self.api_base = (
            api_base
            or os.getenv("AZURE_API_BASE")
            or os.getenv("AZURE_AI_API_BASE")
            or self.proxy_api_base
        )
        self.api_version = api_version or os.getenv("AZURE_API_VERSION") or os.getenv("LITELLM_API_VERSION")

        self.use_proxy = self.proxy_api_base is not None

        if self.use_proxy:
            if OpenAI is None:
                raise ImportError(
                    "openai is required for LiteLLM proxy usage. Install it with `pip install openai`."
                )
            if self.proxy_api_key is None:
                raise RuntimeError(
                    "No LiteLLM proxy API key found. Set LITELLM_API_KEY or OPENAI_API_KEY to use a LiteLLM proxy."
                )
        else:
            if completion is None:
                raise ImportError(
                    "litellm is required for LitellmClassifier. Install it with `pip install litellm`."
                )

            if self.api_key is None:
                raise RuntimeError(
                    "No LLM API key found. Set AZURE_API_KEY, AZURE_AI_API_KEY, OPENAI_API_KEY, or LITELLM_API_KEY to use LitellmClassifier."
                )

            if self.model_name.startswith("azure_ai/") and self.api_base is None:
                raise RuntimeError(
                    "No Azure AI endpoint found. Set AZURE_API_BASE, AZURE_AI_API_BASE, LITELLM_API_BASE, or OPENAI_BASE_URL to use azure_ai models."
                )

    def analyze(self, ticket: Ticket) -> TriageAnalysis:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert ticket routing assistant for an IT support organization in a banking system. "
                    "Analyze the ticket title and description and provide a single JSON response. "
                    "The response must include category, priority, suggested_team, suggested_department, summary, next_step, and rationale. "
                    "Use only the allowed categories: bug, feature, support, requirement, question, unknown. "
                    "Use only the allowed priorities: low, medium, high, critical. "
                    f"Use only one of these departments for suggested_department: {', '.join(KNOWN_DEPARTMENTS)}. "
                    "Route all tickets to the IT support area using suggested_team=\"it-support-team\" unless there is a clear reason to escalate elsewhere. "
                    "Write summary, next_step, and rationale in German. Keep each of them concise and limited to one short sentence. "
                    "Return valid JSON only, without any additional explanation."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Ticket title: {ticket.title}\n"
                    f"Ticket description: {ticket.description}\n"
                    f"Requested category: {ticket.category or 'not provided'}\n"
                    f"Requested priority: {ticket.priority or 'not provided'}\n"
                    f"Existing team context: {ticket.team or 'not provided'}\n"
                    f"Preferred assignee: {ticket.assignee or 'not provided'}\n"
                    f"Due date: {ticket.due_at or 'not provided'}\n"
                    f"Tags: {', '.join(ticket.tags) if ticket.tags else 'not provided'}"
                ),
            },
        ]

        if self.use_proxy:
            client = OpenAI(
                api_key=self.proxy_api_key,
                base_url=self.proxy_api_base,
            )
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
        else:
            response = completion(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                max_tokens=400,
                api_key=self.api_key,
                api_base=self.api_base,
                api_version=self.api_version,
                response_format={"type": "json_object"},
            )

        raw_text = self._extract_text(response)
        parsed = self._parse_json(raw_text)

        category = self._parse_category(parsed.get("category", "unknown"))
        priority = self._parse_priority(parsed.get("priority", "medium"))
        suggested_team = str(parsed.get("suggested_team", "it-support-team")).strip() or "it-support-team"
        suggested_department = normalize_department(
            parsed.get("suggested_department"),
            fallback=infer_department_from_text(
                f"{ticket.title} {ticket.description}",
                fallback=ticket.department,
            ),
        )
        next_step = str(parsed.get("next_step", "Ticket manuell prüfen.")).strip()
        summary = str(parsed.get("summary", f"KI-gestützte Triage für Ticket: {ticket.title}")).strip()
        rationale = str(parsed.get("rationale", "KI-Empfehlung wurde anhand der Routing-Vorgaben erstellt.")).strip()

        return TriageAnalysis(
            predicted_category=category,
            category_confidence=float(parsed.get("category_confidence", 0.75)),
            predicted_priority=priority,
            priority_confidence=float(parsed.get("priority_confidence", 0.7)),
            summary=summary,
            suggested_team=suggested_team,
            suggested_department=suggested_department,
            next_step=next_step,
            rationale=rationale,
            model_version=f"litellm-{self.model_name}",
            analyzed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def _extract_text(self, response: object) -> str:
        if response is None:
            return ""

        content = None

        if hasattr(response, "choices"):
            choices = getattr(response, "choices") or []
            if len(choices) > 0:
                choice = choices[0]
                message = getattr(choice, "message", None)
                if message is not None:
                    content = getattr(message, "content", None)

        if content is None:
            try:
                content = response["choices"][0]["message"]["content"]
            except Exception:
                content = None

        if content is None:
            content = str(response)

        return content or ""

    def _parse_json(self, content: str) -> dict:
        if not content:
            raise ValueError("Received empty response from LitellmClassifier")

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.S)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

            # Fallback for truncated JSON responses: salvage known fields if present.
            recovered = self._recover_partial_json(content)
            if recovered:
                return recovered

            raise ValueError(f"Unable to parse LLM response as JSON: {content!r}")

    def _recover_partial_json(self, content: str) -> dict:
        supported_keys = [
            "category",
            "priority",
            "suggested_team",
            "suggested_department",
            "summary",
            "next_step",
            "rationale",
            "category_confidence",
            "priority_confidence",
        ]

        recovered: dict[str, str | float] = {}

        for key in supported_keys:
            string_match = re.search(rf'"{key}"\s*:\s*"([^"]*)"', content)
            if string_match:
                recovered[key] = string_match.group(1).strip()
                continue

            float_match = re.search(rf'"{key}"\s*:\s*([0-9]+(?:\.[0-9]+)?)', content)
            if float_match:
                try:
                    recovered[key] = float(float_match.group(1))
                except ValueError:
                    continue

        return recovered

    def _parse_category(self, category_text: str) -> TicketCategory:
        normalized = str(category_text).strip().lower()
        if normalized in {category.value for category in TicketCategory}:
            return TicketCategory(normalized)
        return TicketCategory.UNKNOWN

    def _parse_priority(self, priority_text: str) -> TicketPriority:
        normalized = str(priority_text).strip().lower()
        if normalized in {priority.value for priority in TicketPriority}:
            return TicketPriority(normalized)
        return TicketPriority.MEDIUM
