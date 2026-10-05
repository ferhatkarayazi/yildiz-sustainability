import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, Rect, String
from reportlab.graphics.charts.piecharts import Pie

def generate_pdf_report(selected_company, company_df):
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
    
    # Tipografi ve Stil Tanımları
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    section_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=17,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=8,
        spaceAfter=8
    )
    sub_heading = ParagraphStyle(
        'SubHeading',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#334155'),
        spaceBefore=10,
        spaceAfter=6
    )
    kpi_title_style = ParagraphStyle(
        'KpiTitle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748B')
    )
    kpi_val_style = ParagraphStyle(
        'KpiVal',
        parent=styles['Normal'],
        fontSize=13,
        leading=17,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )
    info_box_style = ParagraphStyle(
        'InfoBoxText',
        parent=styles['Normal'],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor('#1E40AF')
    )

    story = []

    # Şirkete ait verisi bulunan yılları dinamik olarak alıp sıralıyoruz
    target_years = sorted(company_df["year"].dropna().unique())

    # Şirketin hiçbir verisi yoksa boş sayfa yerine bilgi notu üret
    if not target_years:
        story.append(Paragraph(f"Sustainability Report — {selected_company}", title_style))
        story.append(Paragraph(f"No records found for {selected_company} in the database.", subtitle_style))
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    for idx, year in enumerate(target_years):
        row_match = company_df[company_df["year"] == year]
        
        # Sayfa Başlığı
        story.append(Paragraph(f"Sustainability Report — {selected_company}", title_style))
        story.append(Paragraph(f"Reporting Year: <b>{year}</b> (Page {idx + 1} of {len(target_years)}) | BigQuery Dataproduct", subtitle_style))
        story.append(Spacer(1, 4))

        data_row = row_match.iloc[0]
        
        # Değerler ve Emisyon Hesaplamaları
        elec_kwh = float(data_row.get("total_electricity_consumed_kwh", 0))
        gas_m3 = float(data_row.get("total_gas_consumed_m3", 0))
        offsite_pct = float(data_row.get("offsite_electricity_percentage", 0))
        renewable_pct = float(data_row.get("renewable_energy_percentage", 0))

        co2_elec_kg = elec_kwh * 0.40
        co2_gas_kg = gas_m3 * 2.00
        total_co2_kg = co2_elec_kg + co2_gas_kg
        total_co2_tons = total_co2_kg / 1000.0

        # =========================================================================
        # TABLO 1: Electricity & Renewable Energy Share
        # =========================================================================
        story.append(Paragraph("Electricity & Renewable Energy Share", section_heading))

        left_flow = [
            [Paragraph("Total Electricity Consumption", kpi_title_style)],
            [Paragraph(f"{elec_kwh:,.0f} kWh".replace(",", "."), kpi_val_style)],
            [Spacer(1, 4)],
            [Paragraph(
                f"<b>Off-Site Electricity Percentage:</b> %{offsite_pct:.1f}<br/>"
                f"<b>Renewable Energy Percentage:</b> %{renewable_pct:.1f}",
                info_box_style
            )]
        ]
        left_table = Table(left_flow, colWidths=[240])
        left_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#EFF6FF')),
            ('BOX', (0, 3), (0, 3), 0.5, colors.HexColor('#BFDBFE')),
            ('PADDING', (0, 3), (0, 3), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        # Sağ Taraf: Donut Chart Çizimi
        chart_drawing = Drawing(260, 130)
        pie = Pie()
        pie.x = 20
        pie.y = 10
        pie.width = 110
        pie.height = 110
        
        chart_data = [offsite_pct, renewable_pct] if (offsite_pct + renewable_pct) > 0 else [1, 0]
        pie.data = chart_data
        pie.labels = [f"%{offsite_pct:.0f}", f"%{renewable_pct:.0f}"]
        pie.slices[0].fillColor = colors.HexColor('#2563EB')
        pie.slices[1].fillColor = colors.HexColor('#10B981')
        chart_drawing.add(pie)

        donut_hole = Circle(75, 65, 28)
        donut_hole.fillColor = colors.white
        donut_hole.strokeColor = colors.white
        chart_drawing.add(donut_hole)

        chart_drawing.add(Rect(155, 75, 8, 8, fillColor=colors.HexColor('#2563EB'), strokeColor=None))
        chart_drawing.add(String(168, 75, "Off-Site Electricity", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor('#1E293B')))
        chart_drawing.add(Rect(155, 55, 8, 8, fillColor=colors.HexColor('#10B981'), strokeColor=None))
        chart_drawing.add(String(168, 55, "Renewable Energy", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor('#1E293B')))

        table1 = Table([[left_table, chart_drawing]], colWidths=[250, 290])
        table1.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(table1)
        story.append(Spacer(1, 14))

        # =========================================================================
        # TABLO 2: Resource Consumption & Carbon Footprint
        # =========================================================================
        story.append(Paragraph("Resource Consumption & Carbon Footprint", section_heading))

        # Elektrik ve Doğalgaz Tüketim Satırları
        res_data = [
            [
                Paragraph("Total Electricity Consumption", kpi_title_style),
                Paragraph("Total Natural Gas Consumption", kpi_title_style)
            ],
            [
                Paragraph(f"{elec_kwh:,.0f} kWh".replace(",", "."), kpi_val_style),
                Paragraph(f"{gas_m3:,.0f} m³".replace(",", "."), kpi_val_style)
            ]
        ]
        res_table = Table(res_data, colWidths=[270, 270])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(res_table)
        story.append(Spacer(1, 10))

        # Emisyon Hesaplama Kartları
        story.append(Paragraph("Carbon Footprint Calculation", sub_heading))

        co2_data = [
            [
                Paragraph("Electricity-Related Emissions (0.40 kg/kWh)", kpi_title_style),
                Paragraph("Natural Gas-Related Emissions (2.00 kg/m³)", kpi_title_style),
                Paragraph("Total Carbon Footprint", kpi_title_style)
            ],
            [
                Paragraph(f"{co2_elec_kg:,.0f} kg CO<sub>2</sub>".replace(",", "."), kpi_val_style),
                Paragraph(f"{co2_gas_kg:,.0f} kg CO<sub>2</sub>".replace(",", "."), kpi_val_style),
                Paragraph(f"{total_co2_tons:,.2f} Ton CO<sub>2</sub>e".replace(",", "."), kpi_val_style)
            ]
        ]
        co2_table = Table(co2_data, colWidths=[180, 180, 180])
        co2_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F0FDF4')),
        ]))
        story.append(co2_table)

        # Son sayfa değilse bir sonraki sayfaya geç
        if idx < len(target_years) - 1:
            story.append(PageBreak())

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()