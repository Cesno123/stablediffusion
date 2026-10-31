package de.spaceage.feinschliff;

import java.net.URLEncoder;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Finds addresses in a text and makes Google Maps links for places. */
final class Places {
    private static final String W = "[A-ZÄÖÜ][a-zäöüß.-]+";
    private static final String STREET = "(?:" + W + "(?:straße|strasse|str\\.|weg|platz|allee|gasse|ring|damm|ufer|chaussee|markt|steig|pfad|berg)"
            + "|" + W + " (?:Straße|Strasse|Str\\.|Weg|Platz|Allee|Gasse|Ring|Damm|Ufer|Chaussee|Markt)"
            + "|(?:Am|An der|Auf dem|Auf der|Im|In der|Zum|Zur|Unter den) " + W + ")";
    // "Hauptstraße 5", "Kölner Str. 12a, 50667 Köln", "An der Alster 3", or just "50667 Köln"
    private static final Pattern ADDRESS = Pattern.compile(
            STREET + " \\d{1,4}[a-zA-Z]?(?:,? \\d{5} " + W + "(?: " + W + ")?)?|\\b\\d{5} " + W + "(?: (?:am|an der|im) " + W + ")?");

    private Places() {}

    static String link(String query) {
        try {
            return "https://www.google.com/maps/search/?api=1&query=" + URLEncoder.encode(query.trim(), "UTF-8");
        } catch (Exception e) {
            return "https://www.google.com/maps/search/?api=1&query=" + query.trim().replace(' ', '+');
        }
    }

    static String link(double lat, double lng) {
        return String.format(java.util.Locale.ROOT, "https://www.google.com/maps/search/?api=1&query=%.6f,%.6f", lat, lng);
    }

    /** The last address in the text that has no maps link after it yet: {start, end}, or null. */
    static int[] lastAddress(String text) {
        Matcher m = ADDRESS.matcher(text);
        int[] found = null;
        while (m.find()) {
            String after = text.substring(m.end(), Math.min(text.length(), m.end() + 60));
            if (!after.trim().startsWith("https://www.google.com/maps")) found = new int[]{m.start(), m.end()};
        }
        return found;
    }

    static final String AI_PROMPT = "Finde im Text alle Orte, Adressen, Lokale, Geschäfte und Treffpunkte, die man auf einer Karte suchen kann. "
            + "Antworte nur mit einer Zeile pro Ort, im Format: genauer Textausschnitt|Suchbegriff für Google Maps "
            + "(mit Stadt, wenn sie aus dem Text hervorgeht). Der Textausschnitt muss wörtlich so im Text stehen. "
            + "Gibt es keinen Ort, antworte nur: KEIN ORT\n\nText:\n<<<\n";
}
