package de.radiotausch

import org.json.JSONArray
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

/** Findet die Stream-Adresse eines Senders über das freie Verzeichnis radio-browser.info. */
object SenderSuche {
    data class Sender(val name: String, val url: String)

    private val server = listOf("all.api.radio-browser.info", "de1.api.radio-browser.info", "fi1.api.radio-browser.info")

    fun finde(name: String): Sender? {
        val suche = URLEncoder.encode(name, "UTF-8")
        var fehler: Exception? = null
        for (host in server) {
            try {
                val url = URL("https://$host/json/stations/search?name=$suche&countrycode=DE" +
                        "&hidebroken=true&order=clickcount&reverse=true&limit=5")
                val verbindung = url.openConnection() as HttpURLConnection
                verbindung.setRequestProperty("User-Agent", "RadioTausch/0.1")
                verbindung.connectTimeout = 10_000
                verbindung.readTimeout = 10_000
                val text = verbindung.inputStream.bufferedReader().use { it.readText() }
                val treffer = JSONArray(text)
                if (treffer.length() == 0) return null
                val erster = treffer.getJSONObject(0)
                val stream = erster.optString("url_resolved").ifBlank { erster.getString("url") }
                return Sender(erster.getString("name").trim(), stream)
            } catch (e: Exception) {
                fehler = e
            }
        }
        throw fehler ?: IllegalStateException("Senderverzeichnis nicht erreichbar")
    }
}
