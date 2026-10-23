package de.spaceage.feinschliff;

/** The tasks, styles and languages, and the prompt for each task. */
final class Tasks {
    static final String[] NAMES = {"Korrigieren", "Umformulieren", "Übersetzen", "Erweitern", "Kürzen", "Antwort vorschlagen"};
    static final String[] STYLE_LABELS = {"Wie ich, nur besser", "Locker", "Förmlich", "Freundlich-bestimmt", "Witzig", "Kurz und knapp", "Instagram mit Emojis"};
    static final String[] STYLES = {"wie ich, nur ohne Fehler und etwas flüssiger", "locker und umgangssprachlich", "förmlich und höflich",
            "freundlich, aber bestimmt", "witzig und schlagfertig", "kurz und knapp, ohne Floskeln", "als Instagram-Bildunterschrift mit passenden Emojis"};
    static final String[] LANGS = {"Englisch", "Deutsch", "Russisch", "Ukrainisch", "Französisch", "Spanisch", "Italienisch", "Türkisch", "Polnisch", "Portugiesisch", "Niederländisch"};

    private static final String KEEP = "Behalte den Ton, die Ausdrucksweise und auch derbe Wörter, Slang und Kraftausdrücke bei. "
            + "Nichts zensieren, nichts abschwächen, keine Hinweise oder Warnungen hinzufügen.";
    private static final String ONLY = "Antworte nur mit dem fertigen Text, ohne Einleitung, ohne Erklärung, ohne Anführungszeichen.";
    static final String OCR = "Auf dem Bild ist Text. Gib den gesamten Text exakt so wieder, wie er dasteht, mit Zeilenumbrüchen, "
            + "in der Originalsprache. Nichts weglassen, nichts verbessern, nichts zensieren. Wenn kein Text zu sehen ist, antworte nur mit: KEIN TEXT";

    private Tasks() {}

    static boolean usesStyle(int task) { return task == 1 || task == 5; }
    static boolean usesLang(int task) { return task == 2; }

    static String prompt(int task, int style, int lang, String text, String context) {
        String s = STYLES[style];
        String job;
        switch (task) {
            case 1: job = "Formuliere den Text um, Stil: " + s + ". Inhalt und Aussage bleiben gleich, die Sprache des Textes bleibt gleich. " + KEEP; break;
            case 2: job = "Übersetze den Text in diese Sprache: " + LANGS[lang] + ". Natürlich und idiomatisch, so wie ein Muttersprachler es schreiben würde. " + KEEP; break;
            case 3: job = "Erweitere den Text: ergänze sinnvollen Inhalt, Details und Zusammenhang, damit er vollständiger und klarer wird, ohne Neues zu erfinden, das dem Text widerspricht. Gleiche Sprache und gleicher Ton. " + KEEP; break;
            case 4: job = "Kürze den Text auf das Wichtigste, ohne Aussage zu verlieren. Gleiche Sprache und gleicher Ton. " + KEEP; break;
            case 5: job = "Schreibe eine passende Antwort auf diesen Text, Stil: " + s + ". In derselben Sprache wie der Text. " + KEEP; break;
            default: job = "Korrigiere Rechtschreibung, Grammatik und Zeichensetzung des Textes. Ändere sonst nichts: gleiche Wörter, gleicher Stil, gleiche Sprache. " + KEEP;
        }
        String ctx = context == null || context.trim().isEmpty() ? "" : "Zusammenhang: " + context.trim() + "\n";
        if (text.length() > 20000) text = text.substring(0, 20000);
        return job + "\n" + ONLY + "\n" + ctx + "\nText:\n<<<\n" + text + "\n>>>";
    }
}
