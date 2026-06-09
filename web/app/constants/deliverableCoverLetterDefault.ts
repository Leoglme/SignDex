/** Message par défaut pour accompagner l’envoi du ZIP ComeUp (modifiable dans l’app). */
export const DELIVERABLE_COVER_LETTER_DEFAULT = `Bonsoir,

Le livrable est prêt : vous trouverez dans l’archive trois versions de signature e-mail (v1, v2, v3), chacune fournie en HTML, JPG et PNG.

Le dossier EXEMPLES contient des images pour vous donner une idée concrète du rendu en situation (comme dans un vrai mail).

Le fichier LISEZMOI-signatures.txt est à lire en priorité : il décrit le rôle de chaque dossier et la marche à suivre pour importer dans Gmail la version que vous préférez, avec des liens cliquables (site, mail, téléphones, réseaux sociaux). Les seules images JPG/PNG seules ne donnent pas des liens cliquables, la procédure détaillée part donc du fichier HTML.

N’hésitez pas à revenir vers moi pour la moindre demande de retouche ou adaptation.

Bonne soirée,
Léo Guillaume
dibodev.fr`

/** Variante “client Apple Mail” : explique les deux formats disponibles (modifiable dans l’app). */
export const DELIVERABLE_COVER_LETTER_APPLE_MAIL = `Bonjour,

Votre livrable est prêt. Comme vous utilisez Apple Mail, vous avez le choix entre deux formats :

1) La version HTML (dossier HTML)
À privilégier si vous voulez des liens cliquables (site, e-mail, téléphone, réseaux sociaux). Vous l’ouvrez dans Safari, vous copiez l’ensemble, puis vous le collez dans Apple Mail (Réglages → Signatures).

2) La version au format Apple (dossier apple-mail)
Le principe : créer une signature vide dans Apple Mail, puis coller le contenu du fichier « signature.mailsignature » fourni dans le fichier de signature de votre Mac. Toute la marche à suivre, pas à pas, est expliquée dans le fichier LISEZMOI-apple-mail.txt.

N’hésitez pas à revenir vers moi pour la moindre demande de retouche ou adaptation.

Bonne journée,
Léo Guillaume
dibodev.fr`

/** Variante “merci + recommandation” (modifiable dans l’app). */
export const DELIVERABLE_COVER_LETTER_REFERRAL = `Bonjour,

Merci pour votre commande.

Votre livrable est prêt : vous trouverez dans l’archive les différentes versions de votre signature e-mail (HTML + images).

Si vous connaissez quelqu’un qui a besoin d’une signature e-mail professionnelle (ou d’un développeur), n’hésitez pas à lui partager mon contact : je serai ravi d’aider.

Bonne journée,
Léo Guillaume
dibodev.fr`
