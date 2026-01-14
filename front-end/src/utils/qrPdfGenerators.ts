import jsPDF from 'jspdf';

interface QRItem {
    item_code: string;
    name: string;
    dataUrl: string; // base64 image data URL
}

interface PDFConfig {
    cols?: number;
    rows?: number;
    cellWidth?: number;
    cellHeight?: number;
    marginX?: number;
    marginY?: number;
    showGrid?: boolean;
}

const CM_TO_PT = 28.3465; // 1 cm = 28.3465 points

export const generateQRCodesPDF = (
    qrItems: QRItem[],
    config: PDFConfig = {}
): jsPDF => {
    // Default configuration
    const {
        cols = 5,
        rows = 2,
        cellWidth = 4 * CM_TO_PT,
        cellHeight = 4 * CM_TO_PT,
        // marginX = 2 * CM_TO_PT,
        marginY = 1 * CM_TO_PT,
        showGrid = false
    } = config;

    // A4 dimensions in points (595.28 x 841.89)
    const pageWidth = 595.28;
    const pageHeight = 841.89;

    // Calculate usable area and starting positions
    const usableWidth = cols * cellWidth;
    const usableHeight = rows * cellHeight;
    const startX = (pageWidth - usableWidth) / 2;
    const startY = marginY;

    // Create PDF
    const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: 'a4'
    });

    const total = qrItems.length;
    const perPage = cols * rows;
    const pages = Math.ceil(total / perPage);

    for (let page = 0; page < pages; page++) {
        if (page > 0) {
            pdf.addPage();
        }

        // Draw QR Codes
        for (let i = 0; i < perPage; i++) {
            const idx = page * perPage + i;
            if (idx >= total) break;

            const row = Math.floor(i / cols);
            const col = i % cols;
            const x = startX + col * cellWidth;
            const y = startY + row * cellHeight;

            const qrItem = qrItems[idx];

            // Draw QR code image
            try {
                pdf.addImage(
                    qrItem.dataUrl,
                    'PNG',
                    x + 5,
                    y + 5,
                    cellWidth - 10,
                    cellHeight - 30,
                    undefined,
                    'FAST'
                );

                // Add item info below QR code
                pdf.setFontSize(8);
                pdf.setFont('helvetica', 'bold');
                pdf.text(qrItem.item_code, x + cellWidth / 2, y + cellHeight - 20, {
                    align: 'center',
                    maxWidth: cellWidth - 10
                });

                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(7);
                const nameLines = pdf.splitTextToSize(qrItem.name, cellWidth - 10);
                pdf.text(nameLines[0] || '', x + cellWidth / 2, y + cellHeight - 10, {
                    align: 'center'
                });
            } catch (error) {
                console.error(`Error adding QR code for item ${qrItem.item_code}:`, error);
            }
        }

        // Draw grid lines (dotted)
        if (showGrid) {
            pdf.setDrawColor(0, 0, 0);
            pdf.setLineDashPattern([2, 4], 0); // Dotted line
            pdf.setLineWidth(0.5);

            // Vertical lines
            for (let c = 0; c <= cols; c++) {
                const xLine = startX + c * cellWidth;
                pdf.line(xLine, startY, xLine, startY + usableHeight);
            }

            // Reset line style
            pdf.setLineDashPattern([], 0);
        }

        // Add page number
        pdf.setFontSize(8);
        pdf.text(
            `Page ${page + 1} of ${pages}`,
            pageWidth / 2,
            pageHeight - marginY / 2,
            { align: 'center' }
        );
    }

    return pdf;
};

export const downloadQRCodesPDF = (
    qrItems: QRItem[],
    filename?: string,
    config?: PDFConfig
): void => {
    const pdf = generateQRCodesPDF(qrItems, config);
    const date = new Date().toISOString().split('T')[0];
    const file = filename || `QRCodes_${date}.pdf`;
    pdf.save(file);
};

export const previewQRCodesPDF = (
    qrItems: QRItem[],
    config?: PDFConfig
): string => {
    const pdf = generateQRCodesPDF(qrItems, config);
    return pdf.output('dataurlstring');
};