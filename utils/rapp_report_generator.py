"""
RAPP Report Generator
Purpose: Generate professional Microsoft-style PDF reports for RAPP Pipeline deliverables

This utility creates customer-facing and account-facing reports with:
- Microsoft Consulting-style branding and formatting
- Executive summaries and detailed analysis sections
- Tables, metrics, and visual hierarchy
- Professional typography and color scheme
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from io import BytesIO

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Microsoft-style color palette
class MSColors:
    """Microsoft brand colors for professional documents."""
    PRIMARY_BLUE = (0, 120, 212)  # Microsoft Blue
    DARK_BLUE = (0, 78, 152)
    LIGHT_BLUE = (0, 164, 239)
    ACCENT_ORANGE = (255, 140, 0)
    ACCENT_GREEN = (16, 124, 16)
    ACCENT_RED = (232, 17, 35)
    NEUTRAL_DARK = (51, 51, 51)
    NEUTRAL_MEDIUM = (102, 102, 102)
    NEUTRAL_LIGHT = (243, 243, 243)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)


class RAPPReportGenerator:
    """
    Professional PDF report generator for RAPP Pipeline deliverables.

    Creates Microsoft Consulting-style documents suitable for:
    - Customer presentations
    - Account team sharing
    - Executive briefings
    - Technical handoffs
    """

    REPORT_TYPES = {
        "discovery": "Discovery Analysis Report",
        "qg1": "Quality Gate 1: Discovery Validation Report",
        "mvp": "MVP Proposal Document",
        "qg2": "Quality Gate 2: Customer Validation Report",
        "code": "Agent Code Generation Report",
        "qg3": "Quality Gate 3: Code Quality Review",
        "deployment": "Deployment Configuration Report",
        "qg4": "Quality Gate 4: Demo Review Report",
        "demo": "Demo Script & Presentation Guide",
        "qg5": "Quality Gate 5: Executive Readiness Review",
        "iteration": "Iteration & Feedback Analysis",
        "production": "Production Deployment Guide",
        "qg6": "Quality Gate 6: Post-Deployment Audit",
        "maintenance": "Scale & Maintenance Plan",
        "executive_summary": "Executive Summary Report",
        "full_pipeline": "Complete Pipeline Report"
    }

    def __init__(self):
        self.use_reportlab = REPORTLAB_AVAILABLE
        self.use_fpdf = FPDF_AVAILABLE and not REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE and not FPDF_AVAILABLE:
            logger.warning("No PDF library available. Install reportlab or fpdf2.")

    def generate_report(
        self,
        report_type: str,
        data: Dict[str, Any],
        customer_name: str,
        project_name: str,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate a professional PDF report.

        Args:
            report_type: Type of report (discovery, qg1, mvp, etc.)
            data: Report data/content
            customer_name: Customer company name
            project_name: Project name
            output_path: Optional path to save the PDF

        Returns:
            PDF content as bytes
        """
        if self.use_reportlab:
            pdf_bytes = self._generate_reportlab(report_type, data, customer_name, project_name)
        elif self.use_fpdf:
            pdf_bytes = self._generate_fpdf(report_type, data, customer_name, project_name)
        else:
            # Fallback to markdown
            pdf_bytes = self._generate_markdown_fallback(report_type, data, customer_name, project_name)

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"Report saved to: {output_path}")

        return pdf_bytes

    def _generate_reportlab(
        self,
        report_type: str,
        data: Dict[str, Any],
        customer_name: str,
        project_name: str
    ) -> bytes:
        """Generate PDF using ReportLab."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Build styles
        styles = self._get_reportlab_styles()
        story = []

        # Title page
        story.extend(self._create_title_page(styles, report_type, customer_name, project_name, data))
        story.append(PageBreak())

        # Content based on report type
        if report_type == "discovery":
            story.extend(self._create_discovery_content(styles, data))
        elif report_type.startswith("qg"):
            story.extend(self._create_quality_gate_content(styles, report_type, data))
        elif report_type == "mvp":
            story.extend(self._create_mvp_content(styles, data))
        elif report_type == "code":
            story.extend(self._create_code_content(styles, data))
        elif report_type == "executive_summary":
            story.extend(self._create_executive_summary_content(styles, data))
        else:
            story.extend(self._create_generic_content(styles, report_type, data))

        # Footer with confidentiality notice
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"<i>Confidential - Prepared for {customer_name} | Generated {datetime.now().strftime('%B %d, %Y')}</i>",
            styles['Footer']
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _get_reportlab_styles(self):
        """Create Microsoft-style paragraph styles for ReportLab."""
        styles = getSampleStyleSheet()

        # Title style - Large, bold, Microsoft Blue
        styles.add(ParagraphStyle(
            name='MSTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=colors.Color(*[c/255 for c in MSColors.PRIMARY_BLUE]),
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))

        # Subtitle
        styles.add(ParagraphStyle(
            name='MSSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.Color(*[c/255 for c in MSColors.NEUTRAL_MEDIUM]),
            spaceAfter=30,
            alignment=TA_LEFT
        ))

        # Section Header
        styles.add(ParagraphStyle(
            name='MSHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.Color(*[c/255 for c in MSColors.DARK_BLUE]),
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderPadding=(0, 0, 5, 0),
            borderWidth=0,
            borderColor=colors.Color(*[c/255 for c in MSColors.PRIMARY_BLUE])
        ))

        # Subsection Header
        styles.add(ParagraphStyle(
            name='MSHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.Color(*[c/255 for c in MSColors.PRIMARY_BLUE]),
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))

        # Body text
        styles.add(ParagraphStyle(
            name='MSBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.Color(*[c/255 for c in MSColors.NEUTRAL_DARK]),
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leading=14
        ))

        # Bullet point
        styles.add(ParagraphStyle(
            name='MSBullet',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.Color(*[c/255 for c in MSColors.NEUTRAL_DARK]),
            leftIndent=20,
            spaceAfter=4,
            bulletIndent=10
        ))

        # Highlight box text
        styles.add(ParagraphStyle(
            name='MSHighlight',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.Color(*[c/255 for c in MSColors.DARK_BLUE]),
            backColor=colors.Color(*[c/255 for c in MSColors.NEUTRAL_LIGHT]),
            borderPadding=10,
            spaceAfter=10
        ))

        # Decision/Status style
        styles.add(ParagraphStyle(
            name='MSDecision',
            parent=styles['Normal'],
            fontSize=16,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=15
        ))

        # Footer
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.Color(*[c/255 for c in MSColors.NEUTRAL_MEDIUM]),
            alignment=TA_CENTER
        ))

        # Metric value
        styles.add(ParagraphStyle(
            name='MSMetric',
            parent=styles['Normal'],
            fontSize=24,
            fontName='Helvetica-Bold',
            textColor=colors.Color(*[c/255 for c in MSColors.PRIMARY_BLUE]),
            alignment=TA_CENTER
        ))

        return styles

    def _create_title_page(self, styles, report_type, customer_name, project_name, data):
        """Create professional title page."""
        story = []

        # Top spacing
        story.append(Spacer(1, 1.5*inch))

        # Report type label
        report_title = self.REPORT_TYPES.get(report_type, "RAPP Pipeline Report")
        story.append(Paragraph(report_title, styles['MSTitle']))

        # Project and customer info
        story.append(Paragraph(f"{project_name}", styles['MSSubtitle']))
        story.append(Paragraph(f"Prepared for: {customer_name}", styles['MSBody']))

        story.append(Spacer(1, 0.5*inch))

        # Date and version
        story.append(Paragraph(
            f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            styles['MSBody']
        ))
        story.append(Paragraph(
            f"<b>Version:</b> 1.0",
            styles['MSBody']
        ))

        # Pipeline step info if available
        if data.get('step'):
            story.append(Paragraph(
                f"<b>Pipeline Step:</b> {data.get('step')} of 14",
                styles['MSBody']
            ))

        story.append(Spacer(1, 1*inch))

        # Executive summary box if available
        if data.get('executive_summary') or data.get('summary'):
            summary = data.get('executive_summary') or data.get('summary', '')
            story.append(Paragraph("Executive Summary", styles['MSHeading2']))
            story.append(Paragraph(self._clean_text(summary), styles['MSHighlight']))

        # Decision banner if this is a quality gate
        if report_type.startswith('qg') and data.get('decision'):
            decision = data.get('decision', 'PENDING')
            decision_color = self._get_decision_color(decision)
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(
                f"<font color='{decision_color}'><b>DECISION: {decision}</b></font>",
                styles['MSDecision']
            ))

        return story

    def _create_discovery_content(self, styles, data):
        """Create discovery report content."""
        story = []

        # Problem Statements
        story.append(Paragraph("Problem Statements", styles['MSHeading1']))
        problems = data.get('problemStatements', data.get('extracted_data', {}).get('problemStatements', []))
        if problems:
            for i, prob in enumerate(problems, 1):
                if isinstance(prob, dict):
                    story.append(Paragraph(f"<b>Problem {i}:</b> {prob.get('problem', '')}", styles['MSBody']))
                    if prob.get('severity'):
                        story.append(Paragraph(f"Severity: {prob.get('severity')}", styles['MSBullet']))
                    if prob.get('businessImpact'):
                        story.append(Paragraph(f"Business Impact: {prob.get('businessImpact')}", styles['MSBullet']))
                else:
                    story.append(Paragraph(f"• {prob}", styles['MSBullet']))

        # Stakeholders
        story.append(Paragraph("Key Stakeholders", styles['MSHeading1']))
        stakeholders = data.get('stakeholders', data.get('extracted_data', {}).get('stakeholders', []))
        if stakeholders:
            table_data = [['Name', 'Role', 'Influence', 'Enthusiasm']]
            for s in stakeholders:
                if isinstance(s, dict):
                    table_data.append([
                        s.get('name', ''),
                        s.get('role', ''),
                        s.get('influenceLevel', ''),
                        s.get('enthusiasm', '')
                    ])
            story.append(self._create_table(table_data))

        # Data Sources
        story.append(Paragraph("Data Sources", styles['MSHeading1']))
        sources = data.get('dataSources', data.get('extracted_data', {}).get('dataSources', []))
        if sources:
            table_data = [['System', 'Type', 'Access Level', 'Complexity']]
            for s in sources:
                if isinstance(s, dict):
                    table_data.append([
                        s.get('systemName', ''),
                        s.get('dataType', ''),
                        s.get('accessLevel', ''),
                        s.get('integrationComplexity', '')
                    ])
            story.append(self._create_table(table_data))

        # Success Criteria
        story.append(Paragraph("Success Criteria", styles['MSHeading1']))
        criteria = data.get('successCriteria', data.get('extracted_data', {}).get('successCriteria', []))
        if criteria:
            table_data = [['Metric', 'Current', 'Target', 'Measurement']]
            for c in criteria:
                if isinstance(c, dict):
                    table_data.append([
                        c.get('metric', ''),
                        c.get('currentValue', ''),
                        c.get('targetValue', ''),
                        c.get('measurementMethod', '')
                    ])
            story.append(self._create_table(table_data))

        # Next Steps
        story.append(Paragraph("Recommended Next Steps", styles['MSHeading1']))
        next_steps = data.get('nextSteps', data.get('extracted_data', {}).get('nextSteps', []))
        if next_steps:
            for step in next_steps:
                story.append(Paragraph(f"• {step}", styles['MSBullet']))

        return story

    def _create_quality_gate_content(self, styles, gate_type, data):
        """Create quality gate report content."""
        story = []

        gate_names = {
            'qg1': 'Discovery Validation',
            'qg2': 'Customer Validation (Scope Lock)',
            'qg3': 'Code Quality Review',
            'qg4': 'Demo Review (Waiter Pattern)',
            'qg5': 'Executive Readiness',
            'qg6': 'Post-Deployment Audit'
        }

        # Gate Overview
        story.append(Paragraph(f"Quality Gate: {gate_names.get(gate_type, gate_type.upper())}", styles['MSHeading1']))

        # Decision with color coding
        decision = data.get('decision', 'PENDING')
        decision_color = self._get_decision_color(decision)
        story.append(Paragraph(
            f"<font color='{decision_color}'><b>Decision: {decision}</b></font>",
            styles['MSDecision']
        ))

        # Overall Score
        if data.get('overallScore'):
            story.append(Paragraph(f"Overall Score: {data.get('overallScore')}/10", styles['MSBody']))

        # Category Scores
        scores = data.get('scores', data.get('categoryScores', {}))
        if scores:
            story.append(Paragraph("Evaluation Criteria", styles['MSHeading2']))
            table_data = [['Criterion', 'Score', 'Notes']]
            for criterion, value in scores.items():
                if isinstance(value, dict):
                    score = value.get('score', value.get('passed', 'N/A'))
                    notes = value.get('notes', value.get('issues', ''))
                    if isinstance(notes, list):
                        notes = '; '.join(str(n) for n in notes[:2])
                    table_data.append([self._format_criterion_name(criterion), str(score), str(notes)[:50]])
                else:
                    table_data.append([self._format_criterion_name(criterion), str(value), ''])
            story.append(self._create_table(table_data))

        # Strengths
        strengths = data.get('strengths', data.get('keyStrengths', []))
        if strengths:
            story.append(Paragraph("Strengths", styles['MSHeading2']))
            for s in strengths:
                story.append(Paragraph(f"✓ {s}", styles['MSBullet']))

        # Concerns
        concerns = data.get('concerns', [])
        if concerns:
            story.append(Paragraph("Concerns", styles['MSHeading2']))
            for c in concerns:
                story.append(Paragraph(f"⚠ {c}", styles['MSBullet']))

        # Recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Recommendations", styles['MSHeading2']))
            for r in recommendations:
                story.append(Paragraph(f"→ {r}", styles['MSBullet']))

        # Next Step
        if data.get('nextStep'):
            story.append(Paragraph("Next Step", styles['MSHeading2']))
            story.append(Paragraph(data.get('nextStep'), styles['MSHighlight']))

        return story

    def _create_mvp_content(self, styles, data):
        """Create MVP proposal content."""
        story = []

        # If we have a full document, parse and display it
        if data.get('document'):
            story.extend(self._parse_markdown_to_reportlab(styles, data['document']))
        else:
            # Build from structured data
            story.append(Paragraph("MVP Overview", styles['MSHeading1']))

            # Features
            features = data.get('features', {})
            if features:
                story.append(Paragraph("MVP Features", styles['MSHeading2']))

                if features.get('p0'):
                    story.append(Paragraph("<b>P0 - Must Have (Critical)</b>", styles['MSBody']))
                    for f in features['p0']:
                        story.append(Paragraph(f"• {f}", styles['MSBullet']))

                if features.get('p1'):
                    story.append(Paragraph("<b>P1 - Should Have (Important)</b>", styles['MSBody']))
                    for f in features['p1']:
                        story.append(Paragraph(f"• {f}", styles['MSBullet']))

                if features.get('p2'):
                    story.append(Paragraph("<b>P2 - Could Have (Nice to Have)</b>", styles['MSBody']))
                    for f in features['p2']:
                        story.append(Paragraph(f"• {f}", styles['MSBullet']))

            # Out of Scope
            out_of_scope = data.get('outOfScope', [])
            if out_of_scope:
                story.append(Paragraph("Explicitly Out of Scope (Phase 2+)", styles['MSHeading2']))
                for item in out_of_scope:
                    story.append(Paragraph(f"• {item}", styles['MSBullet']))

            # Success Metrics
            metrics = data.get('successMetrics', [])
            if metrics:
                story.append(Paragraph("Success Metrics", styles['MSHeading2']))
                table_data = [['Metric', 'Current', 'Target']]
                for m in metrics:
                    if isinstance(m, dict):
                        table_data.append([m.get('metric', ''), m.get('current', ''), m.get('target', '')])
                story.append(self._create_table(table_data))

            # Timeline
            if data.get('estimatedDays'):
                story.append(Paragraph("Timeline", styles['MSHeading2']))
                story.append(Paragraph(f"Estimated Development: {data.get('estimatedDays')} business days", styles['MSBody']))

        return story

    def _create_code_content(self, styles, data):
        """Create code generation report content."""
        story = []

        story.append(Paragraph("Agent Code Generation", styles['MSHeading1']))

        # Agent Info
        story.append(Paragraph("Agent Details", styles['MSHeading2']))
        story.append(Paragraph(f"<b>Agent Name:</b> {data.get('agent_name', 'N/A')}", styles['MSBody']))
        story.append(Paragraph(f"<b>Class Name:</b> {data.get('class_name', 'N/A')}", styles['MSBody']))
        story.append(Paragraph(f"<b>File Name:</b> {data.get('file_name', 'N/A')}", styles['MSBody']))

        # Features
        features = data.get('features_implemented', [])
        if features:
            story.append(Paragraph("Implemented Features", styles['MSHeading2']))
            for f in features:
                story.append(Paragraph(f"✓ {f}", styles['MSBullet']))

        # Code snippet (truncated for report)
        if data.get('code'):
            story.append(Paragraph("Generated Code Preview", styles['MSHeading2']))
            code_preview = data['code'][:1000] + "..." if len(data.get('code', '')) > 1000 else data.get('code', '')
            # Escape special characters for PDF
            code_preview = code_preview.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"<font face='Courier' size='8'>{code_preview}</font>", styles['MSBody']))

        story.append(Paragraph("Note: Full code file attached separately.", styles['Footer']))

        return story

    def _create_executive_summary_content(self, styles, data):
        """Create executive summary content."""
        story = []

        story.append(Paragraph("Executive Summary", styles['MSHeading1']))

        if data.get('summary'):
            story.append(Paragraph(self._clean_text(data['summary']), styles['MSBody']))

        # Key Metrics
        if data.get('metrics'):
            story.append(Paragraph("Key Metrics", styles['MSHeading2']))
            metrics = data['metrics']
            table_data = [['Metric', 'Value']]
            for k, v in metrics.items():
                table_data.append([self._format_criterion_name(k), str(v)])
            story.append(self._create_table(table_data))

        # Progress
        if data.get('progress_percent') is not None:
            story.append(Paragraph("Pipeline Progress", styles['MSHeading2']))
            story.append(Paragraph(f"{data['progress_percent']}% Complete", styles['MSMetric']))
            story.append(Paragraph(f"Current Step: {data.get('current_step', 'N/A')} - {data.get('current_step_name', '')}", styles['MSBody']))

        return story

    def _create_generic_content(self, styles, report_type, data):
        """Create generic content for unspecified report types."""
        story = []

        story.append(Paragraph("Report Details", styles['MSHeading1']))

        # Iterate through data and format
        for key, value in data.items():
            if key in ['status', 'action', 'generated_at', 'evaluatedAt']:
                continue

            formatted_key = self._format_criterion_name(key)

            if isinstance(value, dict):
                story.append(Paragraph(formatted_key, styles['MSHeading2']))
                for k, v in value.items():
                    story.append(Paragraph(f"<b>{self._format_criterion_name(k)}:</b> {v}", styles['MSBody']))
            elif isinstance(value, list):
                story.append(Paragraph(formatted_key, styles['MSHeading2']))
                for item in value:
                    if isinstance(item, dict):
                        story.append(Paragraph(f"• {json.dumps(item)}", styles['MSBullet']))
                    else:
                        story.append(Paragraph(f"• {item}", styles['MSBullet']))
            else:
                story.append(Paragraph(f"<b>{formatted_key}:</b> {value}", styles['MSBody']))

        return story

    def _create_table(self, data: List[List[str]]) -> Table:
        """Create a styled table."""
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(*[c/255 for c in MSColors.PRIMARY_BLUE])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.Color(*[c/255 for c in MSColors.NEUTRAL_DARK])),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(*[c/255 for c in MSColors.NEUTRAL_LIGHT])]),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(*[c/255 for c in MSColors.NEUTRAL_MEDIUM])),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    def _parse_markdown_to_reportlab(self, styles, markdown_text: str) -> list:
        """Convert markdown text to ReportLab elements."""
        story = []
        lines = markdown_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
            elif line.startswith('# '):
                story.append(Paragraph(line[2:], styles['MSHeading1']))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['MSHeading2']))
            elif line.startswith('### '):
                story.append(Paragraph(f"<b>{line[4:]}</b>", styles['MSBody']))
            elif line.startswith('- ') or line.startswith('* '):
                story.append(Paragraph(f"• {line[2:]}", styles['MSBullet']))
            elif line.startswith('|'):
                # Skip table rows for now (complex parsing)
                continue
            else:
                # Clean up markdown formatting
                cleaned = self._clean_text(line)
                if cleaned:
                    story.append(Paragraph(cleaned, styles['MSBody']))

        return story

    def _clean_text(self, text: str) -> str:
        """Clean text for PDF rendering."""
        if not text:
            return ""
        # Convert markdown bold to HTML bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        # Convert markdown italic
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
        # Remove markdown links but keep text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # Escape special characters
        text = text.replace('&', '&amp;')
        return text

    def _format_criterion_name(self, name: str) -> str:
        """Format criterion name to readable form."""
        # Convert camelCase to Title Case
        formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        # Convert snake_case to Title Case
        formatted = formatted.replace('_', ' ')
        return formatted.title()

    def _get_decision_color(self, decision: str) -> str:
        """Get color for decision text."""
        decision_upper = decision.upper()
        if decision_upper in ['PASS', 'PROCEED', 'APPROVE', 'GREEN']:
            return '#107C10'  # Microsoft Green
        elif decision_upper in ['FAIL', 'REJECT', 'RED']:
            return '#E81123'  # Microsoft Red
        elif decision_upper in ['CLARIFY', 'REVISE', 'POLISH', 'YELLOW', 'MINOR_REVISIONS']:
            return '#FF8C00'  # Microsoft Orange
        else:
            return '#0078D4'  # Microsoft Blue

    def _generate_fpdf(self, report_type, data, customer_name, project_name) -> bytes:
        """Fallback PDF generation using FPDF."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 24)
        pdf.set_text_color(*MSColors.PRIMARY_BLUE)

        # Title
        report_title = self.REPORT_TYPES.get(report_type, "RAPP Pipeline Report")
        pdf.cell(0, 15, report_title, ln=True)

        pdf.set_font('Helvetica', '', 14)
        pdf.set_text_color(*MSColors.NEUTRAL_MEDIUM)
        pdf.cell(0, 10, project_name, ln=True)
        pdf.cell(0, 10, f"Prepared for: {customer_name}", ln=True)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)

        pdf.ln(10)

        # Content
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(*MSColors.NEUTRAL_DARK)

        content = json.dumps(data, indent=2, default=str)
        pdf.multi_cell(0, 6, content[:3000])

        return pdf.output()

    def _generate_markdown_fallback(self, report_type, data, customer_name, project_name) -> bytes:
        """Generate markdown as fallback when no PDF library available."""
        report_title = self.REPORT_TYPES.get(report_type, "RAPP Pipeline Report")

        md = f"""# {report_title}

**Project:** {project_name}
**Customer:** {customer_name}
**Date:** {datetime.now().strftime('%B %d, %Y')}

---

## Report Data

```json
{json.dumps(data, indent=2, default=str)}
```

---

*Note: Install reportlab or fpdf2 for professional PDF generation.*
"""
        return md.encode('utf-8')


# Convenience function for direct use
def generate_rapp_report(
    report_type: str,
    data: Dict[str, Any],
    customer_name: str,
    project_name: str,
    output_path: Optional[str] = None
) -> bytes:
    """
    Generate a professional RAPP Pipeline report.

    Args:
        report_type: Type of report (discovery, qg1-qg6, mvp, code, etc.)
        data: Report data/content
        customer_name: Customer company name
        project_name: Project name
        output_path: Optional path to save the PDF

    Returns:
        PDF content as bytes
    """
    generator = RAPPReportGenerator()
    return generator.generate_report(report_type, data, customer_name, project_name, output_path)
