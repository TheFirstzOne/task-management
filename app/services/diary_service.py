"""
DiaryService — Business logic for daily work diary
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.repositories.diary_repo import DiaryRepository
from app.models.diary import DiaryEntry


class DiaryService:

    def __init__(self, db: Session) -> None:
        self.repo = DiaryRepository(db)

    def create_entry(self, content: str) -> DiaryEntry:
        return self.repo.create(content)

    def get_all_entries(self) -> List[DiaryEntry]:
        return self.repo.get_all()

    def get_entries_grouped(self) -> Dict[str, List[DiaryEntry]]:
        return self.repo.get_grouped_by_date()

    def update_entry(self, entry_id: int, content: str) -> Optional[DiaryEntry]:
        return self.repo.update(entry_id, content)

    def delete_entry(self, entry_id: int) -> bool:
        return self.repo.delete(entry_id)

    def export_to_word(self, filepath: str) -> str:
        """Export all diary entries to a Word document. Returns filepath."""
        from docx import Document
        from docx.shared import Pt, Inches

        doc = Document()

        # Page setup A4
        section = doc.sections[0]
        section.page_height = Inches(11.69)
        section.page_width = Inches(8.27)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)

        entries = self.repo.get_all()  # newest first

        if not entries:
            doc.add_paragraph("ยังไม่มีบันทึกการทำงาน")
            doc.save(filepath)
            return filepath

        for i, entry in enumerate(entries):
            if i > 0:
                doc.add_paragraph()
                doc.add_paragraph("=" * 80)

            # Date header
            date_str = entry.created_at.strftime("%d/%m/%Y %H:%M:%S")
            date_para = doc.add_paragraph()
            date_run = date_para.add_run(f"\U0001f4c5 วันที่: {date_str}")
            date_run.bold = True
            date_run.font.size = Pt(12)

            # Content
            content_para = doc.add_paragraph()
            content_run = content_para.add_run(entry.content)
            content_run.font.size = Pt(11)

        doc.save(filepath)
        return filepath
