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
 */
class SpotifyFernbedienung(
    context: Context,
    private val main: Handler,
    private val beiLiedwechsel: () -> Unit,
) {
    private val sitzungen = context.getSystemService(MediaSessionManager::class.java)
    private val zugriff = ComponentName(context, MedienZugriff::class.java)
    private var controller: MediaController? = null
    private var letztesLied: String? = null

    private val callback = object : MediaController.Callback() {
        override fun onMetadataChanged(metadata: MediaMetadata?) {
            val lied = schluessel(metadata) ?: return
            if (lied != letztesLied) {
                letztesLied = lied
                beiLiedwechsel()
            }
        }

        override fun onSessionDestroyed() = trenne()
    }

    private fun suche(): MediaController? {
        controller?.let { return it }
        val gefunden = try {
            sitzungen.getActiveSessions(zugriff).firstOrNull { it.packageName == SPOTIFY }
        } catch (e: SecurityException) {
            null // Benachrichtigungszugriff fehlt
        } ?: return null
        gefunden.registerCallback(callback, main)
        controller = gefunden
        letztesLied = schluessel(gefunden.metadata)
        return gefunden
    }

    fun verfuegbar() = suche() != null

    fun spieltGerade() = controller?.playbackState?.state == PlaybackState.STATE_PLAYING

    /** Gibt false zurück, wenn Spotify gerade nicht erreichbar ist. */
    fun spiele(): Boolean {
        val c = suche() ?: return false
        letztesLied = schluessel(c.metadata)
        c.transportControls.play()
        return true
    }

    fun pausiere() {
        suche()?.transportControls?.pause()
    }

    fun beende() = trenne()

    private fun trenne() {
        controller?.unregisterCallback(callback)
        controller = null
    }

    private fun schluessel(m: MediaMetadata?): String? {
        m ?: return null
        val titel = m.getString(MediaMetadata.METADATA_KEY_TITLE) ?: return null
        return titel + "|" + m.getString(MediaMetadata.METADATA_KEY_ARTIST)
    }

    companion object {
        const val SPOTIFY = "com.spotify.music"
    }
}
