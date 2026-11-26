"""Génère la présentation PowerPoint officielle de l'équipe Dev space ICT pour la Finale SAFINUM 2026."""
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

NAVY = RGBColor(15, 23, 42)
EMERALD = RGBColor(16, 185, 129)
DARK_EMERALD = RGBColor(5, 150, 105)
GOLD = RGBColor(245, 158, 11)
SLATE = RGBColor(51, 65, 85)
LIGHT_BG = RGBColor(248, 250, 252)
WHITE = RGBColor(255, 255, 255)
MUTED = RGBColor(148, 163, 184)


def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, title: str, subtitle: str = ""):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.15))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.18), Inches(10.5), Inches(0.5))
    p = tb.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(25)
    p.font.bold = True
    p.font.color.rgb = WHITE

    if subtitle:
        tb2 = slide.shapes.add_textbox(Inches(0.6), Inches(0.68), Inches(11.5), Inches(0.35))
        p2 = tb2.text_frame.paragraphs[0]
        p2.text = subtitle
        p2.font.size = Pt(13)
        p2.font.color.rgb = EMERALD

    badge = slide.shapes.add_textbox(Inches(10.6), Inches(0.3), Inches(2.2), Inches(0.4))
    bp = badge.text_frame.paragraphs[0]
    bp.text = "DEV SPACE ICT"
    bp.alignment = PP_ALIGN.RIGHT
    bp.font.size = Pt(13)
    bp.font.bold = True
    bp.font.color.rgb = GOLD


def add_card(slide, left, top, width, height, title, bullets, accent=EMERALD):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = accent
    card.line.width = Pt(1.75)

    tb = slide.shapes.add_textbox(Inches(left + 0.25), Inches(top + 0.16), Inches(width - 0.5), Inches(height - 0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(15.5)
    p0.font.bold = True
    p0.font.color.rgb = NAVY
    p0.space_after = Pt(7)

    for b in bullets:
        p = tf.add_paragraph()
        p.text = f"• {b}"
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE
        p.space_after = Pt(4)


def build_deck(out_path: Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    img_dir = out_path.parent / "images"

    # SLIDE 1 — Cover
    s1 = prs.slides.add_slide(blank)
    set_bg(s1, NAVY)
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.0), Inches(4.8), Inches(0.5))
    pill.fill.solid()
    pill.fill.fore_color.rgb = DARK_EMERALD
    pill.line.fill.background()
    p_pill = pill.text_frame.paragraphs[0]
    p_pill.text = "SAFINUM INNOVATE CHALLENGE 2026 • FINALE"
    p_pill.alignment = PP_ALIGN.CENTER
    p_pill.font.size = Pt(12)
    p_pill.font.bold = True
    p_pill.font.color.rgb = WHITE

    tb = s1.shapes.add_textbox(Inches(0.8), Inches(1.85), Inches(8.6), Inches(2.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "SAFINUM LINGUA"
    p1.font.size = Pt(58)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p2 = tf.add_paragraph()
    p2.text = "L'Infrastructure Linguistique Universelle pour la Finance Numérique au Cameroun"
    p2.font.size = Pt(23)
    p2.font.color.rgb = EMERALD

    logo_path = img_dir / "dev_space_ict_logo.jpg"
    if logo_path.exists():
        s1.shapes.add_picture(str(logo_path), Inches(9.7), Inches(1.2), width=Inches(2.8))

    tb_team = s1.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(11.5), Inches(1.5))
    tf_t = tb_team.text_frame
    tf_t.word_wrap = True
    pt1 = tf_t.paragraphs[0]
    pt1.text = "Équipe : Dev space ICT"
    pt1.font.size = Pt(22)
    pt1.font.bold = True
    pt1.font.color.rgb = GOLD
    pt2 = tf_t.add_paragraph()
    pt2.text = "9 Langues (Ewondo, Fulfulde, Duálá, Ɓasaá, Ghɔmálá, Mə̀dûmbà, Pidgin, FR, EN)  •  USSD + Mobile/Web ui_translation + Modèles IA locaux"
    pt2.font.size = Pt(14.5)
    pt2.font.color.rgb = MUTED

    # SLIDE 2 — Problématique & Vision
    s2 = prs.slides.add_slide(blank)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "1. Le Défi : De la Traduction Isolée à l'Infrastructure", "Pourquoi une couche linguistique réutilisable est indispensable")
    add_card(s2, 0.6, 1.5, 5.9, 2.5, "Le Constat Terrain", [
        "Des millions de Camerounais exclus par la barrière linguistique et la terminologie bancaire complexe.",
        "Traduire chaque application séparément est coûteux, lent et non maintenable.",
        "USSD impose GSM-7 strict (182 septets) ; Web & Mobile exigent un contrat ui_translation + lecture vocale claire.",
    ], accent=GOLD)
    add_card(s2, 6.8, 1.5, 5.9, 2.5, "Notre Réponse : Safinum Lingua", [
        "Un middleware REST unique (POST /middleware) gérant USSD conversationnel ET Mobile/Web ui_translation (89 clés).",
        "Modèles IA locaux hors-ligne : correction de phrases T5 + CTranslate2 cameroon-int8 + OPUS-MT-Bantu/Mul.",
        "Moteur phonétique IPA/TTS garantissant une prononciation fidèle sur la Lecture Vocale du sandbox.",
    ], accent=EMERALD)
    add_card(s2, 0.6, 4.3, 12.1, 2.6, "Valeur Ajoutée pour les Institutions Financières", [
        "Zéro modification du code source bancaire existant (intégration via Safinum Gateway + X-Trace-Id).",
        "Complémentarité totale : API REST universelle + Traducteur IA (3001) + Mode Mot-à-Mot (3002) + Extension Chrome.",
        "Architecture prête pour la v2 : SMS asynchrone (160/153 septets), ATM/GAB (multiples 5 000) et IVR (audio 16/8 kHz).",
    ], accent=NAVY)

    # SLIDE 3 — Architecture Technique (Diagramme visuel)
    s3 = prs.slides.add_slide(blank)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "2. Architecture Technique & Flux Gateway", "Interopérabilité multicanale et traçabilité de bout en bout")
    arch_png = img_dir / "safinum_architecture.png"
    if arch_png.exists():
        s3.shapes.add_picture(str(arch_png), Inches(0.6), Inches(1.35), width=Inches(12.1))

    # SLIDE 4 — Double Contrat d'Intégration (Diagramme visuel)
    s4 = prs.slides.add_slide(blank)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "3. Contrats Officiels USSD & Mobile/Web (ui_translation)", "Conformité à 100 % avec le bac à sable SAFINUM (safinum.cm/sandbox/docs)")
    ctr_png = img_dir / "safinum_integration_contracts.png"
    if ctr_png.exists():
        s4.shapes.add_picture(str(ctr_png), Inches(0.6), Inches(1.45), width=Inches(12.1))

    # SLIDE 5 — Pipeline IA, Correction de Phrases & Phonétique (Diagramme visuel)
    s5 = prs.slides.add_slide(blank)
    set_bg(s5, NAVY)
    add_header(s5, "4. Pipeline IA Hybride, Correction T5 & Phonétique Vocale", "Modèles locaux hors-ligne téléchargés + protection financière stricte")
    pipe_png = img_dir / "safinum_ai_phonetics_pipeline.png"
    if pipe_png.exists():
        s5.shapes.add_picture(str(pipe_png), Inches(0.55), Inches(1.35), width=Inches(12.2))

    # SLIDE 6 — Parcours Multicanal Interopérable (Diagramme visuel)
    s6 = prs.slides.add_slide(blank)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "5. Parcours Multicanal Interopérable (Scénario 9)", "Continuité USSD -> Mobile -> Web sans rupture ni double exécution")
    mc_png = img_dir / "safinum_multicanal.png"
    if mc_png.exists():
        s6.shapes.add_picture(str(mc_png), Inches(0.55), Inches(1.4), width=Inches(12.2))

    # SLIDE 7 — 10 Scénarios du Jury
    s7 = prs.slides.add_slide(blank)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "6. Validation Complète des 10 Scénarios du Jury", "Tests automatisés pytest : 10 scénarios, 89 clés UI × 9 langues, GSM-7 & Phonétique")
    add_card(s7, 0.6, 1.5, 5.9, 5.3, "Scénarios 1 à 5", [
        "1. Consultation du solde : GET /accounts/{phone} (y compris sans le mot 'solde')",
        "2. Transfert avec confirmation : 2 tours stricts (X-Trace-Id distinct)",
        "3. Demande de frais : GET /fees (grille exacte 50 / 150 / 400 / 1%)",
        "4. Historique des opérations : GET /transactions (USSD + Web/Mobile)",
        "5. Correction avant confirmation : POST /transactions/{id}/update",
    ], accent=EMERALD)
    add_card(s7, 6.8, 1.5, 5.9, 5.3, "Scénarios 6 à 10", [
        "6. Requête ambiguë : CLARIFICATION_NEEDED (jamais de supposition)",
        "7. Solde insuffisant : INSUFFICIENT_FUNDS traduit en langue nationale",
        "8. Changement de langue : LANGUAGE_SWITCH persistant sur la session",
        "9. Parcours multicanal : USSD -> Mobile -> Web sur le même compte",
        "10. Terminologie financière : bulles help.* & TERM_EXPLANATION pédagogiques",
    ], accent=NAVY)

    # SLIDE 8 — Interfaces Live, Studio & Voix Homme Unique
    s_ui = prs.slides.add_slide(blank)
    set_bg(s_ui, LIGHT_BG)
    add_header(s_ui, "7. Studio Lingua & Écosystème Web (3000 / 3001 / 3002)", "7 langues camerounaises, voix d'homme unique (91–124 Hz), noms & FCFA protégés")
    cap_dir = img_dir / "captures"
    ui_shots = [
        ("Studio Lingua (/studio)", cap_dir / "ui_studio_3000.png", 0.55, 1.45, 5.95),
        ("Diagnostics Middleware (3000)", cap_dir / "ui_middleware_3000.png", 6.8, 1.45, 5.95),
        ("Traducteur IA T5 + CT2 (3001)", cap_dir / "ui_google_3001.png", 0.55, 4.4, 5.95),
        ("Mode Mot-à-Mot Lexical (3002)", cap_dir / "ui_mot_a_mot_3002.png", 6.8, 4.4, 5.95),
    ]
    for label, p, lx, ty, w in ui_shots:
        tb_cap = s_ui.shapes.add_textbox(Inches(lx), Inches(ty - 0.25), Inches(w), Inches(0.28))
        pc = tb_cap.text_frame.paragraphs[0]
        pc.text = label
        pc.font.size = Pt(10.5)
        pc.font.bold = True
        pc.font.color.rgb = NAVY
        if p.exists():
            s_ui.shapes.add_picture(str(p), Inches(lx), Inches(ty + 0.03), width=Inches(w), height=Inches(2.55))

    # SLIDE 9 — Simulateurs Officiels du Bac à Sable SAFINUM
    s_sbx = prs.slides.add_slide(blank)
    set_bg(s_sbx, LIGHT_BG)
    add_header(s_sbx, "8. Connexion aux Simulateurs Officiels SAFINUM", "USSD (*123#), Mobile Banking & Web Banking via POST /middleware")
    sbx_shots = [
        ("Simulateur USSD (/sandbox/ussd)", cap_dir / "sandbox_ussd.png", 0.55, 1.65, 3.85),
        ("Simulateur Mobile (/sandbox/channel/mobile)", cap_dir / "sandbox_mobile.png", 4.72, 1.65, 3.85),
        ("Simulateur Web (/sandbox/channel/web)", cap_dir / "sandbox_web.png", 8.9, 1.65, 3.85),
    ]
    for label, p, lx, ty, w in sbx_shots:
        tb_cap = s_sbx.shapes.add_textbox(Inches(lx), Inches(ty - 0.28), Inches(w), Inches(0.3))
        pc = tb_cap.text_frame.paragraphs[0]
        pc.text = label
        pc.font.size = Pt(11)
        pc.font.bold = True
        pc.font.color.rgb = NAVY
        if p.exists():
            s_sbx.shapes.add_picture(str(p), Inches(lx), Inches(ty + 0.04), width=Inches(w))

    # SLIDE 10 — Scalabilité & Déploiement
    s8 = prs.slides.add_slide(blank)
    set_bg(s8, NAVY)
    add_header(s8, "9. Scalabilité, Déploiement & Vision", "Prêt pour la production et l'inclusion financière nationale")
    add_card(s8, 0.6, 1.5, 4.0, 4.6, "Déploiement Immédiat", [
        "FastAPI + Uvicorn asynchrone (< 50 ms)",
        "Modèles IA 100 % locaux hors-ligne (CT2 int8, OPUS-MT, T5, MMS-TTS)",
        "Exposition HTTPS instantanée (ngrok / cloudflared)",
        "Suite pytest complète validée après chaque changement",
    ], accent=EMERALD)
    add_card(s8, 4.8, 1.5, 4.0, 4.6, "Feuille de Route v2", [
        "SMS asynchrone : compteur exact de segments GSM-7 (160/153)",
        "ATM / GAB : saisie numérique & retraits multiples de 5 000 FCFA",
        "IVR Vocal : ASR Whisper/Wav2Vec2 (16/8 kHz) + TTS MMS/phonétique",
        "Extension Chrome v0.3.0 pour services bancaires tiers existants",
    ], accent=GOLD)
    add_card(s8, 9.0, 1.5, 3.7, 4.6, "Impact Dev space ICT", [
        "Inclusion des populations non francophones/anglophones",
        "Réduction de la fraude grâce aux alertes comprises & lues",
        "Infrastructure mutualisée pour toutes les banques & fintechs CEMAC",
    ], accent=EMERALD)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    print(f"Presentation generee : {out_path}")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "docs" / "Safinum_Lingua_Presentation_Dev_Space_ICT.pptx"
    build_deck(out)
