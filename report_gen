import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(full_df):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    kpi_title_style = ParagraphStyle(
        'KpiTitle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )
    kpi_val_style = ParagraphStyle(
        'KpiVal',
        parent=styles['Normal'],
        fontSize=12,
        leading=15,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A'),
        alignment=1
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    header_cell_style = ParagraphStyle(
        'HeaderCellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []

    # 1. Başlık
    story.append(Paragraph("Sustainability Data Platform — Executive Summary", title_style))
    story.append(Paragraph("Consolidated emissions and energy consumption data across all entities.", subtitle_style))
    story.append(Spacer(1, 4))

    # 2. Konsolide KPI Hesaplamaları
    total_elec = float(full_df["total_electricity_consumed_kwh"].sum())
    total_gas = float(full_df["total_gas_consumed_m3"].sum())
    avg_renewable = float(full_df["renewable_energy_percentage"].mean())

    co2_elec_kg = total_elec * 0.40
    co2_gas_kg = total_gas * 2.00
    total_co2_tons = (co2_elec_kg + co2_gas_kg) / 1000.0

    # KPI Kartları
    kpi_data = [
        [
            Paragraph("TOTAL ELECTRICITY", kpi_title_style),
            Paragraph("TOTAL NATURAL GAS", kpi_title_style),
            Paragraph("AVG RENEWABLE SHARE", kpi_title_style),
            Paragraph("TOTAL CARBON FOOTPRINT", kpi_title_style)
        ],
        [
            Paragraph(f"{total_elec:,.0f} kWh".replace(",", "."), kpi_val_style),
            Paragraph(f"{total_gas:,.0f} m³".replace(",", "."), kpi_val_style),
            Paragraph(f"%{avg_renewable:.1f}", kpi_val_style),
            Paragraph(f"{total_co2_tons:,.2f} Ton CO₂e".replace(",", "."), kpi_val_style)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # 3. Detay Tablosu
    story.append(Paragraph("<b>Breakdown by Entity and Reporting Period</b>", ParagraphStyle('Heading', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#0F172A'), spaceAfter=6)))

    table_data = [[
        Paragraph("Company", header_cell_style),
        Paragraph("Year", header_cell_style),
        Paragraph("Electricity (kWh)", header_cell_style),
        Paragraph("Renewable %", header_cell_style),
        Paragraph("Gas (m³)", header_cell_style),
        Paragraph("CO₂ Total (Ton)", header_cell_style),
    ]]

    for _, row in full_df.sort_values(by=["company_name", "year"], ascending=[True, False]).iterrows():
        elec = float(row.get("total_electricity_consumed_kwh", 0))
        gas = float(row.get("total_gas_consumed_m3", 0))
        row_co2_tons = ((elec * 0.40) + (gas * 2.00)) / 1000.0

        table_data.append([
            Paragraph(str(row["company_name"]), cell_style),
            Paragraph(str(int(row["year"])), cell_style),
            Paragraph(f"{elec:,.0f}".replace(",", "."), cell_style),
            Paragraph(f"%{float(row.get('renewable_energy_percentage', 0)):.1f}", cell_style),
            Paragraph(f"{gas:,.0f}".replace(",", "."), cell_style),
            Paragraph(f"{row_co2_tons:,.2f}".replace(",", "."), cell_style),
        ])

    detail_table = Table(table_data, colWidths=[120, 45, 95, 80, 95, 105])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))

    story.append(detail_table)
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()