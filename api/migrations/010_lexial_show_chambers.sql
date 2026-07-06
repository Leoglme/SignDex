-- Chambers : l'image définitive (chambers-2026.png) est en place → on affiche le logo Chambers pour LEXIAL.
-- Le seed historique mettait show_chambers=0 (du temps du placeholder flou) ; on corrige l'organisation
-- existante (prod + local). Sur une base neuve, LEXIAL n'existe pas encore ici (0 ligne) puis le seed le
-- crée déjà avec show_chambers=1 — donc cette migration ne fait rien de plus.
UPDATE organizations SET show_chambers = 1 WHERE slug = 'lexial';
