# quittances/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
import calendar


class QuittancePDFGenerator:
    """Générateur de PDF pour les quittances de loyer avec support multi-locataires"""

    def __init__(self, quittance):
        self.quittance = quittance
        self.contrat = quittance.contrat

        # ============================================================
        # GESTION MULTI-LOCATAIRES
        # ============================================================
        # Vérifier si le contrat utilise le nouveau système
        if hasattr(self.contrat, 'locataires') and self.contrat.locataires.exists():
            # Nouveau système : plusieurs locataires via ManyToMany
            self.locataires = self.contrat.get_tous_locataires()
            self.locataire_principal = self.contrat.get_locataire_principal()
        else:
            # Ancien système : un seul locataire via FK
            self.locataires = [self.contrat.locataire] if self.contrat.locataire else []
            self.locataire_principal = self.contrat.locataire

        self.appartement = self.contrat.appartement
        self.immeuble = self.appartement.immeuble

        # Configuration des styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configuration des styles personnalisés compacts"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            leading=11,
            fontName='Helvetica'
        ))

    def generate_pdf(self):
        """Génère le PDF de la quittance sur une seule page"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm
        )

        story = []

        # En-tête compact
        story.extend(self._create_header())
        story.append(Spacer(1, 30))

        # Titre
        story.append(Paragraph("QUITTANCE DE LOYER", self.styles['CustomTitle']))
        story.append(Spacer(1, 40))

        # Propriétaire et locataire côte à côte
        story.extend(self._create_owner_tenant_info())
        story.append(Spacer(1, 10))

        # Détails de la location (compact)
        story.extend(self._create_rental_details())
        story.append(Spacer(1, 40))

        # Tableau des montants
        story.extend(self._create_amounts_table())
        story.append(Spacer(1, 40))

        # Texte légal compact
        story.extend(self._create_legal_text())
        story.append(Spacer(1, 55))

        # Signature
        story.extend(self._create_signature())

        # Génération du PDF
        doc.build(story, onFirstPage=self._add_page_number)

        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def _create_header(self):
        """Crée l'en-tête du document"""
        elements = []

        # Informations du propriétaire (récupérées depuis l'appartement)
        proprietaire = self.appartement.proprietaire

        if proprietaire:
            if proprietaire.raison_sociale:
                proprio_nom = proprietaire.raison_sociale
            else:
                proprio_nom = f"{proprietaire.prenom} {proprietaire.nom}"
            proprio_tel = proprietaire.telephone
            proprio_email = proprietaire.email
        else:
            proprio_nom = "PROPRIÉTAIRE"
            proprio_tel = "Téléphone non renseigné"
            proprio_email = "Email non renseigné"

        header_data = [
            [proprio_nom, f"Quittance N° {self.quittance.numero}"],
            [f"Tél: {proprio_tel}", f"Date: {datetime.now().strftime('%d/%m/%Y')}"],
            [proprio_email, ""],
        ]

        header_table = Table(header_data, colWidths=[10 * cm, 8 * cm])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))

        elements.append(header_table)
        return elements

    def _create_owner_tenant_info(self):
        """Informations propriétaire et locataire(s) côte à côte"""
        elements = []

        # ============================================================
        # PROPRIÉTAIRE
        # ============================================================
        proprietaire = self.appartement.proprietaire

        if proprietaire:
            if proprietaire.raison_sociale:
                owner_text = f"""
                <b>PROPRIÉTAIRE</b><br/>
                <b>{proprietaire.raison_sociale}</b><br/>
                {proprietaire.prenom} {proprietaire.nom}<br/>
                Tél: {proprietaire.telephone}<br/>
                Email: {proprietaire.email}
                """
            else:
                owner_text = f"""
                <b>PROPRIÉTAIRE</b><br/>
                <b>{proprietaire.prenom} {proprietaire.nom}</b><br/>
                Tél: {proprietaire.telephone}<br/>
                Email: {proprietaire.email}
                """
        else:
            owner_text = """
            <b>PROPRIÉTAIRE</b><br/>
            <b>Non renseigné</b><br/>
            Informations à compléter
            """

        # ============================================================
        # LOCATAIRE(S) - GESTION MULTI-LOCATAIRES
        # ============================================================
        if len(self.locataires) == 0:
            # Aucun locataire
            tenant_text = """
            <b>LOCATAIRE</b><br/>
            <b>Non renseigné</b><br/>
            """
        elif len(self.locataires) == 1:
            # Un seul locataire
            locataire = self.locataires[0]
            tenant_text = f"""
            <b>LOCATAIRE</b><br/>
            <b>{locataire.prenom} {locataire.nom}</b><br/>
            {self.immeuble.adresse}<br/>
            Appartement {self.appartement.numero}<br/>
            {self.immeuble.code_postal} {self.immeuble.ville}<br/>
            Tél: {locataire.telephone}<br/>
            Email: {locataire.email}
            """
        else:
            # Plusieurs locataires
            tenant_text = "<b>LOCATAIRES</b><br/>"

            for i, locataire in enumerate(self.locataires):
                # Marquer le locataire principal
                if locataire == self.locataire_principal:
                    tenant_text += f"<b>{locataire.prenom} {locataire.nom}</b> (Principal)<br/>"
                else:
                    tenant_text += f"<b>{locataire.prenom} {locataire.nom}</b><br/>"

            # Ajouter l'adresse une seule fois
            tenant_text += f"""
            {self.immeuble.adresse}<br/>
            Appartement {self.appartement.numero}<br/>
            {self.immeuble.code_postal} {self.immeuble.ville}
            """

            # Ajouter les coordonnées du principal
            if self.locataire_principal:
                tenant_text += f"""<br/>
                <i>Contact principal:</i><br/>
                Tél: {self.locataire_principal.telephone}<br/>
                Email: {self.locataire_principal.email}
                """

        # ============================================================
        # CRÉATION DU TABLEAU
        # ============================================================
        info_data = [
            [
                Paragraph(owner_text, self.styles['CustomNormal']),
                Paragraph(tenant_text, self.styles['CustomNormal'])
            ]
        ]

        info_table = Table(info_data, colWidths=[9 * cm, 9 * cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(info_table)
        return elements

    def _create_rental_details(self):
        """Détails de la location en format compact"""
        elements = []

        # Créer un tableau compact pour les détails
        details_data = [
            ["Immeuble:", self.immeuble.nom, "Appartement:", f"N° {self.appartement.numero}"],
            ["Étage:", f"{self.appartement.etage}", "Période:", self._format_mois(self.quittance.mois)],
        ]

        details_table = Table(details_data, colWidths=[3 * cm, 6 * cm, 3 * cm, 6 * cm])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ]))

        elements.append(details_table)
        return elements

    def _create_amounts_table(self):
        """Tableau des montants compact"""
        elements = []

        amounts_data = [
            ["Désignation", "Montant"],
            [f"Loyer hors charges - {self._format_mois(self.quittance.mois)}",
             f"{float(self.quittance.loyer):.2f} €"],
            ["Charges locatives (provision)", f"{float(self.quittance.charges):.2f} €"],
            ["TOTAL PAYÉ", f"{float(self.quittance.total):.2f} €"]
        ]

        amounts_table = Table(amounts_data, colWidths=[12 * cm, 4 * cm])
        amounts_table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Corps
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),

            # Ligne de total
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
            ('ALIGN', (1, -1), (1, -1), 'RIGHT'),

            # Bordures
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#34495e')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#34495e')),

            # Espacement réduit
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        elements.append(amounts_table)
        return elements

    def _create_legal_text(self):
        """Texte légal obligatoire compact avec gestion multi-locataires"""
        elements = []

        # ============================================================
        # ADAPTATION DU TEXTE SELON LE NOMBRE DE LOCATAIRES
        # ============================================================
        if len(self.locataires) == 0:
            locataires_text = "du locataire"
        elif len(self.locataires) == 1:
            locataires_text = f"de {self.locataires[0].prenom} {self.locataires[0].nom}"
        elif len(self.locataires) == 2:
            locataires_text = (
                f"de {self.locataires[0].prenom} {self.locataires[0].nom} "
                f"et {self.locataires[1].prenom} {self.locataires[1].nom}"
            )
        else:
            # 3 locataires ou plus
            noms = [f"{loc.prenom} {loc.nom}" for loc in self.locataires[:-1]]
            locataires_text = f"de {', '.join(noms)} et {self.locataires[-1].prenom} {self.locataires[-1].nom}"

        legal_text = f"""
        <b>Je soussigné(e), propriétaire du logement désigné ci-dessus, reconnais avoir reçu 
        {locataires_text}, la somme de {float(self.quittance.total):.2f} euros 
        pour le paiement du loyer et des charges de la période du {self.quittance.mois.strftime('%d/%m/%Y')} 
        au {self._get_end_of_month()}, dont le détail figure ci-dessus.</b>
        """

        # Utiliser un style plus compact
        compact_style = ParagraphStyle(
            name='CompactStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=8,
            leading=11,
            fontName='Helvetica'
        )

        elements.append(Paragraph(legal_text, compact_style))

        # Note légale plus petite
        note_text = """
        <i>Cette quittance annule tous reçus qui auraient pu être délivrés précédemment 
        en cas d'acomptes versés sur la période concernée. Article 21 de la loi du 6 juillet 1989.</i>
        """

        note_style = ParagraphStyle(
            name='NoteStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=0,
            leading=10,
            fontName='Helvetica',
            textColor=colors.HexColor('#666666')
        )

        elements.append(Paragraph(note_text, note_style))
        return elements

    def _create_signature(self):
        """Bloc signature compact"""
        elements = []

        signature_data = [
            [f"Fait à {self.immeuble.ville}, le {datetime.now().strftime('%d/%m/%Y')}", "Signature du propriétaire:"],
            ["", ""],
            ["", ""],
            ["", ""],
        ]

        signature_table = Table(signature_data, colWidths=[9 * cm, 9 * cm])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # ('LINEBELOW', (1, -1), (1, -1), 1, colors.black),
            ('BOX', (0, 0), (1, -1), 1, colors.black),
        ]))

        elements.append(signature_table)
        return elements

    def _format_mois(self, date_mois):
        """Formate le mois en français"""
        mois_fr = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return f"{mois_fr[date_mois.month]} {date_mois.year}"

    def _get_end_of_month(self):
        """Retourne le dernier jour du mois de la quittance"""
        year = self.quittance.mois.year
        month = self.quittance.mois.month
        last_day = calendar.monthrange(year, month)[1]
        return f"{last_day:02d}/{month:02d}/{year}"

    def _add_page_number(self, canvas, doc):
        """Ajoute le numéro de page"""
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(A4[0] - 2 * cm, 1 * cm, text)

        # Pied de page
        footer_text = "Document généré automatiquement - Système de gestion locative"
        canvas.setFont('Helvetica', 8)
        canvas.drawCentredString(A4[0] / 2, 0.5 * cm, footer_text)