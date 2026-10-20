package de.radiotausch

import android.content.ComponentName
import android.content.Context
import android.media.MediaMetadata
import android.media.session.MediaController
import android.media.session.MediaSessionManager
import android.media.session.PlaybackState
import android.os.Handler

/**
 * Steuert die Spotify-App wie die Tasten am Kopfhörer (Play/Pause) und
 * merkt, wenn Spotify zum nächsten Lied springt. Braucht keine Spotify-Schnittstelle.
 *
 * Spotify hat oft mehrere Mediensitzungen gleichzeitig und tauscht sie beim Abspielen
 * aus. Deshalb wird bei jeder Abfrage neu geschaut, statt sich eine Sitzung zu merken.
 */
class SpotifyFernbedienung(
    context: Context,
    private val main: Handler,
    private val beiLiedwechsel: () -> Unit,
) {
    private val sitzungen = context.getSystemService(MediaSessionManager::class.java)
    private val zugriff = ComponentName(context, MedienZugriff::class.java)
    private var beobachtet: MediaController? = null
    private var letztesLied: String? = null

    private val callback = object : MediaController.Callback() {
        override fun onMetadataChanged(metadata: MediaMetadata?) = pruefeLied(metadata)
        override fun onSessionDestroyed() {
            beobachtet = null
        }
    }

    private val sitzungsWechsel = MediaSessionManager.OnActiveSessionsChangedListener { waehle() }

    init {
        try {
            sitzungen.addOnActiveSessionsChangedListener(sitzungsWechsel, zugriff, main)
        } catch (e: SecurityException) {
            // Benachrichtigungszugriff fehlt, wird in der App angezeigt
        }
    }

    private fun spotifySitzungen(): List<MediaController> = try {
        sitzungen.getActiveSessions(zugriff).filter { it.packageName == SPOTIFY }
    } catch (e: SecurityException) {
        emptyList()
    }

    /** Die Spotify-Sitzung, die gerade spielt, sonst die erste. */
    private fun waehle(): MediaController? {
        val alle = spotifySitzungen()
        val beste = alle.firstOrNull { laeuft(it) } ?: alle.firstOrNull()
        if (beste?.sessionToken != beobachtet?.sessionToken) {
            beobachtet?.unregisterCallback(callback)
            beobachtet = beste
            beste?.registerCallback(callback, main)
        }
        return beste
    }

    private fun laeuft(c: MediaController) = when (c.playbackState?.state) {
        PlaybackState.STATE_PLAYING,
        PlaybackState.STATE_BUFFERING,
        PlaybackState.STATE_CONNECTING,
        PlaybackState.STATE_SKIPPING_TO_NEXT -> true
        else -> false
    }

    fun verfuegbar() = waehle() != null

    fun spieltGerade() = spotifySitzungen().any { laeuft(it) }

    /** Kurzer Text für die Anzeige in der App. */
    fun zustand(): String {
        val c = waehle() ?: return "Spotify: nicht gefunden – siehe Einrichtung, Schritt 2"
        val titel = titel(c.metadata)?.let { " – $it" }.orEmpty()
        return if (spieltGerade()) "Spotify: spielt ▶$titel" else "Spotify: pausiert ⏸$titel"
    }

    /** Gibt false zurück, wenn Spotify gerade nicht erreichbar ist. */
    fun spiele(): Boolean {
        val c = waehle() ?: return false
        letztesLied = titel(c.metadata)
        c.transportControls.play()
        return true
    }

    fun pausiere() {
        spotifySitzungen().forEach { it.transportControls.pause() }
    }

    /** Regelmäßig aufrufen: erkennt Liedwechsel auch dann, wenn Spotify die Sitzung austauscht. */
    fun pruefe() = pruefeLied(waehle()?.metadata)

    private fun pruefeLied(metadata: MediaMetadata?) {
        val lied = titel(metadata) ?: return
        if (letztesLied == null) {
            letztesLied = lied
        } else if (lied != letztesLied) {
            letztesLied = lied
            beiLiedwechsel()
        }
    }

    fun beende() {
        sitzungen.removeOnActiveSessionsChangedListener(sitzungsWechsel)
        beobachtet?.unregisterCallback(callback)
        beobachtet = null
    }

    // Nur der Titel: Spotify liefert den Interpreten manchmal erst später nach,
    // das sah vorher wie ein Liedwechsel aus.
    private fun titel(m: MediaMetadata?) = m?.getString(MediaMetadata.METADATA_KEY_TITLE)?.takeIf { it.isNotBlank() }

    companion object {
        const val SPOTIFY = "com.spotify.music"
    }
}
