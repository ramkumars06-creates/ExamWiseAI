"""
Syllabus PDF upload and text extraction endpoint.
Uses PyMuPDF for PDF parsing.
"""
import io
import json
import re
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

router = APIRouter(tags=["syllabus"])


def _extract_units_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Heuristic extraction of units/modules and their topics from raw syllabus text.
    Looks for patterns like 'Unit N:', 'Module N:', 'Chapter N:' etc.
    """
    units = []
    # Patterns for unit headings
    unit_pattern = re.compile(
        r'(?:unit|module|chapter|section)\s*[-:]?\s*(\d+)\s*[:\-–]?\s*(.+)',
        re.IGNORECASE
    )
    lines = text.split('\n')
    current_unit: Dict[str, Any] | None = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        unit_match = unit_pattern.match(line)
        if unit_match:
            if current_unit:
                units.append(current_unit)
            unit_num = unit_match.group(1)
            unit_name = unit_match.group(2).strip().rstrip(':.–-').strip()
            current_unit = {
                "order_index": int(unit_num),
                "name": unit_name or f"Unit {unit_num}",
                "topics": [],
            }
        elif current_unit:
            # Try to detect topic-like lines (not headings, not empty)
            # Lines that are short, sentence-like, and don't start with digits alone
            if len(line) > 5 and len(line) < 200:
                # Skip lines that look like page numbers or short fragments
                if not re.match(r'^\d+$', line) and not re.match(r'^(page|pg\.?)\s*\d+', line, re.I):
                    current_unit["topics"].append({
                        "title": line[:200],
                        "description": "",
                        "difficulty": "medium",
                        "exam_importance": "medium",
                        "estimated_minutes": 60,
                    })

    if current_unit:
        units.append(current_unit)

    # If no units detected, create a single default unit with all lines as topics
    if not units:
        topics = []
        for line in lines:
            line = line.strip()
            if 5 < len(line) < 200:
                topics.append({
                    "title": line[:200],
                    "description": "",
                    "difficulty": "medium",
                    "exam_importance": "medium",
                    "estimated_minutes": 60,
                })
        if topics:
            units.append({
                "order_index": 1,
                "name": "General Topics",
                "topics": topics[:50],  # cap at 50 topics
            })

    return units


@router.post("/api/syllabus/upload")
async def upload_syllabus(
    file: UploadFile = File(...),
    subject_id: int = Form(...),
):
    """
    Upload a PDF syllabus file and extract structured content.
    Returns extracted units and topics without saving to DB
    (caller should use /api/units and /api/topics endpoints to persist).
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 20 MB."
        )

    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF processing library not available."
        )

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not open PDF: {str(e)}"
        )

    full_text_parts = []
    page_count = len(doc)

    for page_num in range(min(page_count, 100)):  # cap at 100 pages
        page = doc[page_num]
        text = page.get_text("text")
        if text:
            full_text_parts.append(text)

    doc.close()
    full_text = "\n".join(full_text_parts)

    if not full_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract text from PDF. It may be a scanned/image PDF."
        )

    # Extract structured content
    extracted_units = _extract_units_from_text(full_text)

    # Truncate topics per unit to keep response manageable
    for unit in extracted_units:
        unit["topics"] = unit["topics"][:20]

    return {
        "subject_id": subject_id,
        "filename": file.filename,
        "page_count": page_count,
        "character_count": len(full_text),
        "units_detected": len(extracted_units),
        "units": extracted_units,
        "raw_text_preview": full_text[:500] + ("..." if len(full_text) > 500 else ""),
    }
