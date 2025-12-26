import os

DIR = "/Users/jasonjia/Documents/industry_policy/agri_energy_demo/data/markdown/belgium/wallonia/extra"

FILES_TO_DELETE = [
    # Translations (German/Dutch)
    "Agrarumwelt- und Klimaschutzmaßnahmen Neu Für 2025.md",
    "Agromilieuklimaatmaatregelen Nieuw voor 2024.md",
    "Basisinkomenssteun Herverdelingsbetaling en aanvullende inkomenssteun voor jonge landbouwers.md",
    "Basisprämie Umverteilungsprämie Zahlung für Junglandwirte Neu Für 2025.md",
    "Definities.md",
    "Definitionen.md",
    "Ecoregeling Nieuw voor 2024.md",
    "GAP 2023-2027 - Beschreibung der Interventionen.md",
    "Gekoppelde steun Nieuw voor 2024.md",
    "Gekopplete Stützung Neu Für 2025.md",
    "GLB 2023-2027 - Beschrijving van interventies.md",
    "Guter landwirtschaftlicher und ökologischer Zustand von Flächen GLÖZ und Grundanforderungen an die Betriebsführung GAB Neu Für 2025.md",
    "Investitionsbeihilfen Neu für 2025.md",
    "Kooperation.md",
    "Kumulierung von Beihilfen.md",
    "Niederlassung von jungen Landwirten.md",
    "Soziale Konditionalität.md",
    "Unterstützung für den ökologischenbiologischen Landbau Neu für 2025.md",
    "Versterkte randvoorwaarden Nieuw voor 2024.md",
    "Zahlung für aus naturbedingten oder anderen spezifischen Gründen benachteiligte Gebiete.md",
    "Zahlungen Natura 2000 Neu für 2024.md",
    "Ökoregelungen.md",

    # Historical Crisis/Old Measures (Pre-2022 context/titles)
    "Aides au transfert de connaissances et aux actions dinformation dans le secteur agricole et sylvicole pour la période 2015-2020.md",
    "Aides pour les employeurs dans les secteurs agricole de la pêche et de laquaculture INONDATIONS juillet 2021.md",
    "Indemnisation des dommages causés par la sécheresse des mois de mai et juin 2015 considérée comme calamité agricole par le fonds de gestion des calami.md",
    "Projets HRA sélectionnés en 2016.md",
    "Projets HRA sélectionnés en 2019.md",
    "Reconnaissance de la sécheresse 2017 comme calamité agricole.md",
    "Reconnaissance de la sécheresse 2018 comme calamité agricole.md",
    "Reconnaissance du gel comme calamité agricole.md",
    "Régime cadre exempté de notification n SA.50488 relatif aux aides aux actions de promotion en faveur des produits agricoles pour la période 2018-2020.md",
    "Régime daide octroyant une de crise en 2021 aux producteurs porcins affectés par la chute des prix dues aux mesures de lutte contre le Covid-19.md",
    "Régime daide pour linstallation des jeunes agriculteurs en Région wallonne dans le programme wallon de développement rural 2007-2013 mesure 112 régime.md",

    # Generic/Landing Pages (Intro only)
    "AII Aides à lInstallation et aux Investissements.md",
    "Aides aux investissements.md",
    "Aides détat.md",
    "Crises et calamités.md",
    "Eco-régimes Nouveauté 2026.md",
    "Conditionnalité sociale.md",
    "Fiches explicatives.md",
    "Installation des jeunes agriculteurs.md",
    "Les projets de coopération.md",
    "Paiement de base paiement redistributif et paiement jeune Nouveauté 2025.md",
    "Paiements Natura 2000.md",
    "Soutien couplé Nouveauté 2026.md",
    "Texte introductif.md",
    "Pac 2023-2027 - Description des interventions.md",
    "Documents à télécharger - FAQ.md"
]

for filename in FILES_TO_DELETE:
    path = os.path.join(DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted: {filename}")
    else:
        print(f"Skipped (not found): {filename}")
