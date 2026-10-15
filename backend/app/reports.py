"""PDF report generation via reportlab."""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart

DANGER = colors.HexColor("#EF4444")
WARNING = colors.HexColor("#F59E0B")
SECONDARY = colors.HexColor("#4ADE80")


def _risk_level(simulation_result: dict) -> tuple:
    m = simulation_result["metrics"]
    if simulation_result["scenario_type"] == "road_closure":
        if m.get("zones_cut_off_entirely", 0) > 0:
            return "HIGH", DANGER
        if m.get("avg_hospital_route_delay_pct", 0) >= 50 or m.get("max_ambulance_delay_min", 0) >= 3:
            return "MEDIUM", WARNING
        if m.get("avg_hospital_route_delay_pct", 0) > 0:
            return "LOW", SECONDARY
        return "MINIMAL", SECONDARY
    else:
        if m.get("population_newly_best_served", 0) == 0:
            return "LOW VALUE", WARNING
        return "POSITIVE", SECONDARY


def generate_report(simulation_result: dict, explanation_text: str, output_path: str) -> str:
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CityMindTitle", parent=styles["Title"],
                                  textColor=colors.HexColor("#09111f"), fontSize=22)
    heading_style = ParagraphStyle("CityMindHeading", parent=styles["Heading2"],
                                    textColor=colors.HexColor("#00A8CC"), spaceBefore=14)
    body_style = styles["BodyText"]
    story = []

    scenario_type = simulation_result["scenario_type"].replace("_", " ").title()
    story.append(Paragraph("CITYMIND", title_style))
    story.append(Paragraph(f"Simulation Report — {scenario_type}", styles["Heading3"]))
    story.append(Paragraph(datetime.now().strftime("Generated %B %d, %Y at %H:%M"), body_style))
    story.append(Spacer(1, 0.5*cm))

    risk_label, risk_color = _risk_level(simulation_result)
    risk_table = Table([["Risk Level", risk_label]], colWidths=[4*cm, 4*cm])
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, 0), risk_color),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(explanation_text, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Predicted Impacts", heading_style))
    metric_rows = [["Metric", "Value"]]
    for k, v in simulation_result["metrics"].items():
        metric_rows.append([k.replace("_", " ").title(), str(v)])
    metrics_table = Table(metric_rows, colWidths=[10*cm, 5*cm])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#09111f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.4*cm))

    detail_key = "hospital_route_detail" if "hospital_route_detail" in simulation_result else "zone_detail"
    detail = simulation_result.get(detail_key, [])
    if detail:
        story.append(Paragraph("Affected Areas", heading_style))
        area_rows = [["Zone", "Population", "Before (min)", "After (min)", "Change"]]
        chart_labels, chart_values = [], []
        for d in detail[:10]:
            if "time_before_min" in d:
                area_rows.append([
                    d["zone"], f"{d['population']:,}", str(d["time_before_min"]),
                    str(d.get("time_after_min", "—")),
                    f"{d.get('delta_pct', 0)}%" if d.get("delta_pct") is not None else "—",
                ])
                chart_labels.append(d["zone"][:12])
                chart_values.append(d.get("delta_pct") or 0)
            else:
                area_rows.append([
                    d["zone"], f"{d['population']:,}",
                    str(d.get("time_to_nearest_existing_min", "—")),
                    str(d.get("time_to_new_facility_min", "—")),
                    "Improved" if d.get("new_facility_becomes_closest") else "No change",
                ])
        area_table = Table(area_rows, colWidths=[4.5*cm, 2.7*cm, 2.6*cm, 2.6*cm, 2.6*cm])
        area_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#09111f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(area_table)
        story.append(Spacer(1, 0.4*cm))

        if chart_values and any(v for v in chart_values):
            story.append(Paragraph("Delay % by Zone (chart)", heading_style))
            drawing = Drawing(400, 180)
            chart = VerticalBarChart()
            chart.x, chart.y = 30, 20
            chart.width, chart.height = 340, 140
            chart.data = [chart_values]
            chart.categoryAxis.categoryNames = chart_labels
            chart.categoryAxis.labels.angle = 30
            chart.categoryAxis.labels.fontSize = 6
            chart.bars[0].fillColor = colors.HexColor("#00D4FF")
            drawing.add(chart)
            story.append(drawing)
            story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Recommendation", heading_style))
    if "recommendation" in simulation_result:
        story.append(Paragraph(simulation_result["recommendation"]["text"], body_style))
    else:
        story.append(Paragraph("See metrics above for coverage impact of the proposed facility placement.", body_style))

    doc.build(story)
    return output_path