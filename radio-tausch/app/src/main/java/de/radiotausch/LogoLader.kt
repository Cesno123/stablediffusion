package de.radiotausch

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.os.Handler
import android.os.Looper
import android.util.LruCache
import android.widget.ImageView
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import kotlin.math.abs

/** Lädt Senderlogos im Hintergrund. Ohne Logo gibt es eine bunte Kachel mit dem Anfangsbuchstaben. */
object LogoLader {
    private const val GROESSE = 144
    private val cache = LruCache<String, Bitmap>(100)
    private val arbeiter = Executors.newFixedThreadPool(4)
    private val main = Handler(Looper.getMainLooper())
    private val farben = intArrayOf(
        0xFF6B4EFF.toInt(), 0xFFFF5C82.toInt(), 0xFF00A88F.toInt(),
        0xFFFF9F1C.toInt(), 0xFF2E86DE.toInt(), 0xFF8E44AD.toInt(),
    )

    fun zeige(ziel: ImageView, name: String, logoUrl: String) {
        ziel.tag = logoUrl
        ziel.setImageBitmap(platzhalter(name))
        if (logoUrl.isBlank()) return
        cache.get(logoUrl)?.let { ziel.setImageBitmap(it); return }
        arbeiter.execute {
            val bild = try { lade(logoUrl) } catch (e: Exception) { null } ?: return@execute
            cache.put(logoUrl, bild)
            main.post { if (ziel.tag == logoUrl) ziel.setImageBitmap(bild) }
        }
    }

    private fun lade(adresse: String): Bitmap? {
        val verbindung = URL(adresse).openConnection() as HttpURLConnection
        verbindung.connectTimeout = 5_000
        verbindung.readTimeout = 5_000
        verbindung.setRequestProperty("User-Agent", "RadioTausch/0.2")
        val daten = verbindung.inputStream.use { it.readBytes() }
        val bild = BitmapFactory.decodeByteArray(daten, 0, daten.size) ?: return null
        if (bild.width < 16) return null // winzige Favicons sehen schlechter aus als der Platzhalter
        // Auf weißen Grund setzen, damit durchsichtige Logos im Dunkelmodus lesbar bleiben
        val ergebnis = Bitmap.createBitmap(GROESSE, GROESSE, Bitmap.Config.ARGB_8888)
        val leinwand = Canvas(ergebnis)
        leinwand.drawColor(Color.WHITE)
        val massstab = minOf(GROESSE.toFloat() / bild.width, GROESSE.toFloat() / bild.height)
        val b = (bild.width * massstab).toInt()
        val h = (bild.height * massstab).toInt()
        leinwand.drawBitmap(
            Bitmap.createScaledBitmap(bild, b, h, true),
            ((GROESSE - b) / 2).toFloat(), ((GROESSE - h) / 2).toFloat(), null
        )
        return ergebnis
    }

    private fun platzhalter(name: String): Bitmap {
        val bild = Bitmap.createBitmap(GROESSE, GROESSE, Bitmap.Config.ARGB_8888)
        val leinwand = Canvas(bild)
        leinwand.drawColor(farben[abs(name.hashCode()) % farben.size])
        val schrift = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = GROESSE * 0.45f
            textAlign = Paint.Align.CENTER
            isFakeBoldText = true
        }
        val buchstabe = name.firstOrNull { it.isLetterOrDigit() }?.uppercase() ?: "?"
        val y = GROESSE / 2f - (schrift.descent() + schrift.ascent()) / 2
        leinwand.drawText(buchstabe, GROESSE / 2f, y, schrift)
        return bild
    }
}
