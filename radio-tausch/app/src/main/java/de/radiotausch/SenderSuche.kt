package de.radiotausch

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

data class Sender(val name: String, val url: String, val logo: String, val info: String)

/** Sucht Sender im freien Verzeichnis radio-browser.info (über 50.000 Sender weltweit). */
object SenderSuche {

    private val server = listOf("all.api.radio-browser.info", "de1.api.radio-browser.info", "fi1.api.radio-browser.info")

    /** Die meistgehörten Sender im Land (Ländercode wie "DE"), für den Start ohne Suchbegriff. */
    fun beliebt(land: String) = abfrage("countrycode=$land&order=clickcount&reverse=true&hidebroken=true&limit=50")

    fun suche(text: String) = abfrage(
        "name=" + URLEncoder.encode(text, "UTF-8") + "&order=clickcount&reverse=true&hidebroken=true&limit=50"
    )

    private fun abfrage(parameter: String): List<Sender> {
        var fehler: Exception? = null
        for (host in server) {
            try {
                val verbindung = URL("https://$host/json/stations/search?$parameter").openConnection() as HttpURLConnection
                verbindung.setRequestProperty("User-Agent", "RadioSwap/0.3")
                verbindung.connectTimeout = 10_000
                verbindung.readTimeout = 10_000
                val treffer = JSONArray(verbindung.inputStream.bufferedReader().use { it.readText() })
                return (0 until treffer.length())
                    .mapNotNull { lies(treffer.getJSONObject(it)) }
                    .distinctBy { it.name.lowercase() } // das Verzeichnis hat viele Doppelte
            } catch (e: Exception) {
                fehler = e
            }
        }
        throw fehler ?: IllegalStateException("Senderverzeichnis nicht erreichbar")
    }

    private fun lies(o: JSONObject): Sender? {
        val name = o.optString("name").trim()
        val url = o.optString("url_resolved").ifBlank { o.optString("url") }
        if (name.isBlank() || url.isBlank()) return null
        val stichworte = o.optString("tags").split(",").map { it.trim() }.filter { it.isNotEmpty() }.take(2)
        val info = (listOf(o.optString("state"), o.optString("country")) + stichworte.joinToString(", "))
            .filter { it.isNotBlank() }
            .joinToString(" · ")
        return Sender(name, url, o.optString("favicon"), info)
    }
}

/** Einstellungen der App. */
object Einstellungen {
    private fun prefs(c: Context) = c.getSharedPreferences("einstellungen", Context.MODE_PRIVATE)

    /** Bei Moderation im Radio Spotify sofort anhalten, statt das Lied zu Ende zu spielen. */
    fun sofortZurueck(c: Context) = prefs(c).getBoolean("sofortZurueck", true)

    fun setzeSofortZurueck(c: Context, an: Boolean) = prefs(c).edit().putBoolean("sofortZurueck", an).apply()

    /** So viele Sekunden muss im Radio Musik laufen, bevor Spotify startet. Höher = unempfindlicher. */
    fun musikSekunden(c: Context) = prefs(c).getInt("musikSekunden", 10)

    fun setzeMusikSekunden(c: Context, sekunden: Int) = prefs(c).edit().putInt("musikSekunden", sekunden).apply()

    /** Nachrichten zur vollen Stunde immer im Radio hören. */
    fun nachrichtenVoll(c: Context) = prefs(c).getBoolean("nachrichtenVoll", true)

    fun setzeNachrichtenVoll(c: Context, an: Boolean) = prefs(c).edit().putBoolean("nachrichtenVoll", an).apply()

    /** Nachrichten zur halben Stunde immer im Radio hören. */
    fun nachrichtenHalb(c: Context) = prefs(c).getBoolean("nachrichtenHalb", false)

    fun setzeNachrichtenHalb(c: Context, an: Boolean) = prefs(c).edit().putBoolean("nachrichtenHalb", an).apply()
}

/** Merkt sich den gewählten Sender. */
object SenderSpeicher {
    private fun prefs(c: Context) = c.getSharedPreferences("sender", Context.MODE_PRIVATE)

    fun lade(c: Context): Sender? {
        val p = prefs(c)
        val url = p.getString("url", null) ?: return null
        return Sender(p.getString("name", "")!!, url, p.getString("logo", "")!!, p.getString("info", "")!!)
    }

    fun speichere(c: Context, s: Sender) {
        prefs(c).edit()
            .putString("name", s.name)
            .putString("url", s.url)
            .putString("logo", s.logo)
            .putString("info", s.info)
            .apply()
    }
}
